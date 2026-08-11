from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from access_control.emergency import EmergencyAccessRequest
from access_control.rbac import has_permission
from audit.hash_chain import create_log_entry
from records.peer_client import get_or_cache_patient

MIN_JUSTIFICATION_LENGTH = 20

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def emergency_access_request_view(request, nhid):
    if not has_permission(request.user, "view_record"):
        return Response(
            {"status": "error", "code": "FORBIDDEN",
             "message": "Only clinical staff can request emergency access"},
            status=status.HTTP_403_FORBIDDEN
        )

    if not request.user.hospital:
        return Response(
            {"status": "error", "code": "NO_HOSPITAL",
             "message": "Hospital not assigned to your account"},
            status=status.HTTP_400_BAD_REQUEST
        )

    justification = request.data.get("justification", "").strip()
    if len(justification) < MIN_JUSTIFICATION_LENGTH:
        return Response(
            {"status": "error", "code": "JUSTIFICATION_TOO_SHORT",
             "message": f"Justification must be at least {MIN_JUSTIFICATION_LENGTH} characters"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # BUG FIX: this used to be a plain Patient.objects.get(nhid=nhid),
    # which only ever looked in THIS hospital's own database. A TUTH
    # doctor requesting emergency access for a patient who only exists
    # in Bir's database got an immediate (and wrong) "no patient found"
    # -- the patient is real, just not cached here yet.
    # get_or_cache_patient checks locally first, then asks every known
    # peer for demographics if not found here, creating a local Patient
    # row from whatever a peer knows -- exactly the case this endpoint
    # needs to support.
    patient = get_or_cache_patient(nhid)
    if not patient:
        return Response(
            {"status": "error", "code": "PATIENT_NOT_FOUND",
             "message": "No patient with this NHID found"},
            status=status.HTTP_404_NOT_FOUND
        )

    emergency_request = EmergencyAccessRequest.objects.create(
        doctor=request.user,
        patient=patient,
        justification=justification,
    )

    create_log_entry(
        actor=request.user,
        action="EMERGENCY_ACCESS_GRANTED",
        patient=patient,
        hospital=request.user.hospital,
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    return Response({
        "status": "success",
        "message": "Emergency access granted for 1 hour",
        "data": {
            "request_id": emergency_request.id,
            "expires_at": emergency_request.expires_at,
        }
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pending_emergency_reviews_view(request):
    if not has_permission(request.user, "verify_audit"):
        return Response(
            {"status": "error", "code": "FORBIDDEN",
             "message": "Only hospital admins can review emergency access"},
            status=status.HTTP_403_FORBIDDEN
        )

    # Only requests filed by THIS admin's own hospital's doctors --
    # an admin should never see another hospital's break-glass activity
    pending = EmergencyAccessRequest.objects.filter(
        reviewed_by_admin=False,
        doctor__hospital=request.user.hospital,
    ).order_by("-requested_at")

    data = [
        {
            "id": req.id,
            "doctor": req.doctor.full_name,
            "patient": req.patient.nhid,
            "justification": req.justification,
            "requested_at": req.requested_at,
            "expires_at": req.expires_at,
            "is_active": req.is_active(),
        }
        for req in pending
    ]

    return Response({"status": "success", "message": "Pending reviews fetched", "data": data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_emergency_reviewed_view(request, request_id):
    if not has_permission(request.user, "verify_audit"):
        return Response(
            {"status": "error", "code": "FORBIDDEN",
             "message": "Only hospital admins can review emergency access"},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        emergency_request = EmergencyAccessRequest.objects.get(id=request_id)
    except EmergencyAccessRequest.DoesNotExist:
        return Response(
            {"status": "error", "code": "NOT_FOUND", "message": "Request not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    # Same hospital-boundary rule as the list view above -- an admin
    # must not be able to mark another hospital's request as reviewed,
    # even if they somehow know its numeric ID
    if emergency_request.doctor.hospital_id != request.user.hospital_id:
        return Response(
            {"status": "error", "code": "FORBIDDEN",
             "message": "This request does not belong to your hospital"},
            status=status.HTTP_403_FORBIDDEN
        )

    emergency_request.reviewed_by_admin = True
    emergency_request.save()

    return Response({"status": "success", "message": "Marked as reviewed", "data": {}})