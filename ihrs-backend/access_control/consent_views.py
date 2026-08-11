from datetime import timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from accounts.models import Hospital, PeerHospital, Patient
from .models import AccessConsent
from audit.hash_chain import create_log_entry
from records.peer_client import broadcast_consent_event
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def grant_consent_view(request):
    # Yo action patient ले matra garna paunxa — afno data ho,
    # doctor/nurse/admin le arू ko tarफबाट consent diना मिल्दैन
    if request.user.role != "patient":
        return Response(
            {"status": "error", "code": "FORBIDDEN",
             "message": "Only Patient can grant consent."},
            status=status.HTTP_403_FORBIDDEN
        )

    if not request.user.patient_profile:
        return Response(
            {"status": "error", "code": "NO_PATIENT_PROFILE",
             "message": "Patient profile is not linked with your account."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # hospital_name identifies EITHER a local Hospital row OR a peer
    # hospital known only through PeerHospital -- no local row is
    # required for the peer case, since the consent table itself now
    # stores the name directly (see AccessConsent.hospital_name).
    hospital_name = request.data.get("hospital_name")
    duration_days = request.data.get("duration_days", 30)  # default 30 din

    if not hospital_name:
        return Response(
            {"status": "error", "code": "MISSING_HOSPITAL",
             "message": "hospital_name is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    is_known_hospital = (
        Hospital.objects.filter(name=hospital_name).exists()
        or PeerHospital.objects.filter(name=hospital_name).exists()
    )
    if not is_known_hospital:
        return Response(
            {"status": "error", "code": "HOSPITAL_NOT_FOUND",
             "message": "Hospital Not Found"},
            status=status.HTTP_404_NOT_FOUND
        )

    # get_or_create: existing consent (pahिले revoke भएको) भए
    # tehi row update garcha, natra naya banaucha
    consent, created = AccessConsent.objects.get_or_create(
        patient=request.user.patient_profile,
        hospital_name=hospital_name,
        defaults={
            "granted": True,
            "expires_at": timezone.now() + timedelta(days=duration_days),
        }
    )

    if not created:
        # existing row thiyo (pahिले revoke bhaeko थियो होला) —
        # refresh garने: active bnaउने ra expiry naya garने
        consent.granted = True
        consent.expires_at = timezone.now() + timedelta(days=duration_days)
        consent.save()

    broadcast_consent_event(
        nhid=consent.patient.nhid,
        hospital_name=consent.hospital_name,
        granted=True,
    )
    patient = request.user.patient_profile

    # Only attaches a real local Hospital object if one exists (the
    # intra-hospital case) -- for a peer-only name, hospital stays
    # None and hospital_name carries the identity instead.
    local_hospital = Hospital.objects.filter(name=hospital_name).first()

    create_log_entry(
        actor=request.user,
        action="CONSENT_GRANTED",
        patient=patient,
        hospital=local_hospital,
        hospital_name=hospital_name,
        ip_address=request.META.get("REMOTE_ADDR"),
    )
    return Response(
        {"status": "success",
         "message": f"consent granted to {hospital_name} ",
         "data": {"expires_at": consent.expires_at, "token": consent.token}},
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_consent_view(request):
    if request.user.role != "patient":
        return Response(
            {"status": "error", "code": "FORBIDDEN",
             "message": "Only patient can revoke the consent."},
            status=status.HTTP_403_FORBIDDEN
        )

    hospital_name = request.data.get("hospital_name")

    try:
        consent = AccessConsent.objects.get(
            patient=request.user.patient_profile,
            hospital_name=hospital_name
        )
    except AccessConsent.DoesNotExist:
        return Response(
            {"status": "error", "code": "CONSENT_NOT_FOUND",
             "message": " No consent record with the Hospital."},
            status=status.HTTP_404_NOT_FOUND
        )

    # DELETE gardैnaun — granted=False matra गर्ने, kina bhane
    # audit/history ko lagi "consent thiyो, pachi revoke bhayo"
    # bhanne record raखनुपर्छ (model design garda yehि decide gareका थियौं)
    consent.granted = False
    consent.save()
    broadcast_consent_event(
        nhid=consent.patient.nhid,
        hospital_name=consent.hospital_name,
        granted=False,
    )
    local_hospital = Hospital.objects.filter(name=consent.hospital_name).first()
    create_log_entry(
    actor=request.user,
    action="CONSENT_REVOKED",
    patient=consent.patient,
    hospital=local_hospital,
    hospital_name=consent.hospital_name,
    ip_address=request.META.get("REMOTE_ADDR"),
    )
    return Response(
        {"status": "success",
         "message": "Consent revoked. "},
        status=status.HTTP_200_OK
    )