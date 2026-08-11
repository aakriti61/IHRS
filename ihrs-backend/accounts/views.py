from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib.auth import authenticate

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


from django.db import transaction
from .models import Patient , CustomUser
from access_control.rbac import has_permission


def generate_nhid():
    """
    Format: NH-00001-BIR (or NH-00001-TUTH, etc.)

    BUG FIX: this used to end in a hardcoded "-KTM" suffix, with only
    the sequential number varying. Because Bir and TUTH each run this
    exact codebase against their OWN separate database (Postgres vs
    MySQL -- see settings_tuth.py), their Patient.id auto-increment
    sequences are completely independent of each other. Both databases
    started counting from 1, so Bir's first patient and TUTH's first
    patient were BOTH assigned "NH-00001-KTM" -- an identical NHID for
    two different people at two different hospitals, even though
    Patient.nhid is declared unique=True (that uniqueness constraint
    only ever applied *within* a single database).

    Fix: suffix with settings.HOSPITAL_CODE instead, which is set
    differently per hospital (see ihrs/settings.py / settings_tuth.py).
    Since the two hospitals now always produce different suffixes,
    their sequential numbers can never collide again, no matter how
    the id sequences line up.
    """
    from django.conf import settings
    hospital_code = getattr(settings, "HOSPITAL_CODE", "BIR")
    last_patient = Patient.objects.order_by("-id").first()
    next_number = (last_patient.id + 1) if last_patient else 1
    return f"NH-{next_number:05d}-{hospital_code}"


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_view(request):
    """
    Ticket-counter model: a patient does NOT self-register. Only
    hospital staff (hospital_admin) can create a patient account --
    this hospital becomes the patient's home hospital, simply because
    it's the one that issued the account. Mirrors create_staff_view's
    exact pattern below: temp password generated here, patient must
    change it on first login (must_change_password=True), admin never
    sets or knows the patient's real password.
    """
    if not has_permission(request.user, "register_patient"):
        return Response({
            "status": "error", "code": "FORBIDDEN",
            "message": "Only hospital staff can register a new patient.",
        }, status=status.HTTP_403_FORBIDDEN)

    if not request.user.hospital:
        return Response({
            "status": "error", "code": "NO_HOSPITAL",
            "message": "Your admin account is not linked to a hospital",
        }, status=status.HTTP_400_BAD_REQUEST)

    data = request.data.copy()

    data["role"] = "patient"
    data.pop("hospital", None)  # patients don't belong to a hospital themselves

    dob = data.pop("dob", None)
    blood_group = data.pop("blood_group", None)
    emergency_contact = data.pop("emergency_contact", None)

    if not all([dob, blood_group, emergency_contact]):
        return Response({
            "status": "error",
            "code": "MISSING_FIELDS",
            "message": "dob, blood_group and emergency_contact are all required",
        }, status=400)

    # Explicit pre-check for Patient.phone -- CustomUser.phone being
    # unique already blocks most duplicates through this endpoint
    # (RegisterSerializer validates it before we get here), but
    # Patient.phone now also carries its own unique constraint (see
    # accounts/models.py). Checking here up front turns a possible raw
    # IntegrityError/500 into a normal, friendly 400 response.
    if Patient.objects.filter(phone=data.get("phone")).exists():
        return Response({
            "status": "error",
            "code": "PHONE_IN_USE",
            "message": "A patient with this phone number is already registered.",
        }, status=400)

    # Front desk never sets the patient's password directly -- same
    # reasoning as create_staff_view: a short-lived temp password is
    # generated here, told to the patient verbally/on a slip, and they
    # must set their own real password on first login.
    temp_password = generate_temp_password()
    data["password"] = temp_password

    serializer = RegisterSerializer(data=data)

    if serializer.is_valid():
        with transaction.atomic():
            patient = Patient.objects.create(
                nhid=generate_nhid(),
                full_name=data.get("full_name"),
                dob=dob,
                blood_group=blood_group,
                phone=data.get("phone"),
                emergency_contact=emergency_contact,
            )
            user = serializer.save()
            user.patient_profile = patient
            user.must_change_password = True
            user.save()

        return Response({
            "status": "success",
            "message": "Patient registered",
            "data": {
                "user": UserSerializer(user).data,
                "nhid": patient.nhid,
                # Returned ONCE, here only -- reception must share this
                # with the patient through a secure/in-person channel.
                "temporary_password": temp_password,
            }
        }, status=201)

    return Response({
        "status": "error",
        "message": serializer.errors
    }, status=400)

@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            "status": "error",
            "code": "VALIDATION_ERROR",
            "message": serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    identifier = serializer.validated_data["identifier"]
    password = serializer.validated_data["password"]

    # authenticate() le internally hamro EmailOrPhoneBackend call garcha
    # (settings.py ko AUTHENTICATION_BACKENDS ma register gareko)
    user = authenticate(request, username=identifier, password=password)

    if user is None:
        return Response({
            "status": "error",
            "code": "INVALID_CREDENTIALS",
            "message": "Phone/Email or password is wrong.",
        }, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({
            "status": "error",
            "code": "ACCOUNT_DISABLED",
            "message": "This account is disabled",
        }, status=status.HTTP_403_FORBIDDEN)

    token, created = Token.objects.get_or_create(user=user)
    return Response({
        "status": "success",
        "message": "Login successful",
        "data": {
            "user": UserSerializer(user).data,
            "token": token.key,
            "must_change_password": user.must_change_password,
        }
    }, status=status.HTTP_200_OK)
    


@api_view(["POST"])
@permission_classes([IsAuthenticated])  # login vayeko user le matra logout garna paos
def logout_view(request):
    # user ko token delete garne — yesले garda purano token invalid huncha,
    # feri login navaesamma kunai API call garna mildaina
    request.user.auth_token.delete()

    return Response({
        "status": "success",
        "message": "Logged out successfully",
    }, status=status.HTTP_200_OK)





import secrets
import string

def generate_temp_password(length=10):
    """
    Generate a random temporary password for a new staff/patient account.
    Uses secrets (not random) — cryptographically secure, same
    reasoning as AccessConsent.token generation.

    NOTE: the actual staff-creation endpoint wired up in urls.py lives
    in accounts/staff_views.py, NOT here -- a duplicate create_staff_view
    used to also exist in this file but was dead code (urls.py never
    imported it), which caused a real bug: editing this copy had zero
    effect on the live endpoint. Removed to prevent that happening again.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not old_password or not new_password:
        return Response({
            "status": "error", "code": "MISSING_FIELDS",
            "message": "old_password and new_password are both required",
        }, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.check_password(old_password):
        return Response({
            "status": "error", "code": "WRONG_PASSWORD",
            "message": "Current password is incorrect",
        }, status=status.HTTP_401_UNAUTHORIZED)

    if len(new_password) < 8:
        return Response({
            "status": "error", "code": "PASSWORD_TOO_SHORT",
            "message": "New password must be at least 8 characters",
        }, status=status.HTTP_400_BAD_REQUEST)

    request.user.set_password(new_password)
    request.user.must_change_password = False
    request.user.save()

    return Response({
        "status": "success",
        "message": "Password changed successfully",
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_phone_view(request):
    new_phone = request.data.get("phone", "").strip()

    if not new_phone:
        return Response(
            {"status": "error", "code": "MISSING_FIELD", "message": "Phone number is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Uniqueness check BEFORE saving -- phone is USERNAME_FIELD, a
    # duplicate would break login for both accounts if saved directly
    if CustomUser.objects.filter(phone=new_phone).exclude(id=request.user.id).exists():
        return Response(
            {"status": "error", "code": "PHONE_IN_USE",
             "message": "This phone number is already linked to another account."},
            status=status.HTTP_400_BAD_REQUEST
        )

    request.user.phone = new_phone
    request.user.save()

    # Keep Patient.phone in sync -- it's a separate field (not a
    # reference to CustomUser.phone), and it's what doctors see on
    # the patient card, so it must never go stale
    if request.user.role == "patient" and request.user.patient_profile:
        request.user.patient_profile.phone = new_phone
        request.user.patient_profile.save()

    return Response({
        "status": "success",
        "message": "Phone number updated.",
        "data": {"user": UserSerializer(request.user).data},
    }, status=status.HTTP_200_OK)

from .models import SiteContact


@api_view(["GET"])
@permission_classes([AllowAny])
def site_contact_view(request):
    contact = SiteContact.objects.first()
    if not contact:
        return Response({"status": "success", "data": None})
    return Response({
        "status": "success",
        "data": {"address": contact.address, "phone": contact.phone, "email": contact.email},
    })