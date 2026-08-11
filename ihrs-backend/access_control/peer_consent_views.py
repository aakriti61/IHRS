# access_control/peer_consent_views.py

from datetime import timedelta

from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from accounts.models import PeerHospital
from records.peer_client import get_or_cache_patient
from .models import AccessConsent


@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def sync_consent(request):

    # =====================================================
    # 1. AUTHENTICATE PEER HOSPITAL
    # =====================================================

    shared_key = request.headers.get("X-Hospital-Key")

    if not shared_key:
        return Response(
            {"status": "error", "message": "Hospital key missing"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    peer = PeerHospital.objects.filter(shared_secret=shared_key).first()

    if not peer:
        return Response(
            {"status": "error", "message": "Unauthorized hospital"},
            status=status.HTTP_403_FORBIDDEN
        )

    # =====================================================
    # 2. RECEIVE DATA
    # =====================================================

    nhid = request.data.get("nhid")
    hospital_name = request.data.get("hospital_name")
    granted = request.data.get("granted")

    if not nhid or not hospital_name:
        return Response(
            {"status": "error", "message": "NHID and hospital_name required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if granted not in [True, False]:
        return Response(
            {"status": "error", "message": "Invalid granted value"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # =====================================================
    # 3. FIND PATIENT
    # =====================================================

    # BUG FIX: this used to be Patient.objects.get(nhid=nhid), which
    # only ever looked in THIS hospital's own database -- so any
    # patient who registered at the OTHER hospital (and was never
    # separately treated here) always 404'd, even though this
    # endpoint's whole purpose is handling cross-hospital consent.
    # get_or_cache_patient checks locally first, then asks peers
    # (including asking back the hospital that's calling us right
    # now) for demographics, and caches a local Patient row.
    patient = get_or_cache_patient(nhid)
    if not patient:
        return Response(
            {"status": "error", "message": "Patient not available in this hospital database"},
            status=status.HTTP_404_NOT_FOUND
        )

    # =====================================================
    # 4. CREATE OR UPDATE CONSENT
    # =====================================================

    consent, created = AccessConsent.objects.get_or_create(
        patient=patient,
        hospital_name=hospital_name,
        defaults={
            "granted": granted,
            "expires_at": timezone.now() + timedelta(days=30)
        }
    )

    if not created:
        consent.granted = granted
        if granted:
            consent.expires_at = timezone.now() + timedelta(days=30)
        consent.save()

    # =====================================================
    # 5. RESPONSE
    # =====================================================

    return Response(
        {
            "status": "success",
            "message": "Consent synchronized",
            "data": {
                "patient": nhid,
                "hospital": hospital_name,
                "granted": consent.granted
            }
        },
        status=status.HTTP_200_OK
    )