import secrets
import string

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import RegisterSerializer, UserSerializer
from access_control.rbac import require_permission


def generate_temp_password(length=10):
    """
    Cryptographically secure random password for a new staff account.
    The admin never chooses this -- it's generated here so the admin
    only ever sees a short-lived value, never a password they picked.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@require_permission("manage_doctors")
def create_staff_view(request):

    role = request.data.get("role")

    # Only doctor, nurse, or receptionist can be created via this endpoint
    if role not in ["doctor", "nurse", "receptionist"]:
        return Response({
            "status": "error",
            "code": "INVALID_ROLE",
            "message": "Role must be 'doctor', 'nurse', or 'receptionist'."
        }, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.hospital:
        return Response({
            "status": "error",
            "code": "NO_HOSPITAL",
            "message": "Your admin account is not linked to a hospital.",
        }, status=status.HTTP_400_BAD_REQUEST)

    data = request.data.copy()

    # Force hospital to be the logged-in admin's hospital
    data["hospital"] = request.user.hospital.id

    # Admin never sets the password directly -- a temporary one is
    # generated here, shown once in the response, then never stored
    # or shown again in plaintext.
    temp_password = generate_temp_password()
    data["password"] = temp_password

    serializer = RegisterSerializer(data=data)

    if serializer.is_valid():
        user = serializer.save()
        user.must_change_password = True
        user.save()

        return Response({
            "status": "success",
            "message": "Staff created successfully",
            "data": {
                "user": UserSerializer(user).data,
                "temporary_password": temp_password,
            },
        }, status=status.HTTP_201_CREATED)

    return Response({
        "status": "error",
        "code": "VALIDATION_ERROR",
        "message": serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)