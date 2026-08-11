from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.models import Patient
from audit.models import AuditLog
from audit.hash_chain import verify_chain_integrity
from access_control.rbac import has_permission


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def audit_logs_view(request, nhid):
    try:
        patient = Patient.objects.get(nhid=nhid)
    except Patient.DoesNotExist:
        return Response({"status": "error", "code": "NOT_FOUND", "message": "Patient not found"}, status=404)

    is_self = (
        request.user.role == "patient"
        and getattr(request.user, "patient_profile", None) == patient
    )
    if not is_self and not has_permission(request.user, "verify_audit"):
        return Response({"status": "error", "code": "FORBIDDEN", "message": "Not allowed"}, status=403)

    if is_self:
        logs = AuditLog.objects.filter(patient=patient).order_by("id")
    else:
        # Hospital admin sees only the slice of this patient's audit
        # trail that involves THEIR OWN hospital -- not the patient's
        # full cross-hospital history. Seeing another hospital's
        # interactions with this patient would leak a relationship
        # the patient never consented to reveal to this admin.
        logs = AuditLog.objects.filter(patient=patient, hospital=request.user.hospital).order_by("id")
        if not logs.exists():
            return Response(
                {"status": "error", "code": "NOT_FOUND",
                 "message": "No activity for this patient at your hospital."},
                status=404
            )

    # BUG FIX: this used to only be initialized inside the `else`
    # branch above, so a patient viewing their OWN audit log
    # (is_self=True) hit an UnboundLocalError on the very first
    # data.append() below -- every patient dashboard load crashed.
    data = []

    for log in logs:
        data.append({
            "id": log.id,
            "action": log.action,
            # FIX: was log.actor.phone -- frontend's "By" column showed
            # raw phone numbers instead of names because this sent the
            # phone as the actor's display value. full_name is what the
            # UI actually expects to render there.
            "actor": log.actor.full_name if log.actor else None,
            "hospital": log.hospital.name if log.hospital else None,
            "timestamp": log.timestamp,
            "ip_address": log.ip_address,
            "hash": log.hash,
            "previous_hash": log.prev_hash,
        })

    return Response({
        "status": "success",
        "message": "Audit log fetched",
        "data": data
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verify_audit_chain_view(request, nhid):
    try:
        patient = Patient.objects.get(nhid=nhid)
    except Patient.DoesNotExist:
        return Response({"status": "error", "code": "NOT_FOUND", "message": "Patient not found"}, status=404)

    if not has_permission(request.user, "verify_audit"):
        return Response({"status": "error", "code": "FORBIDDEN", "message": "Only hospital admins can verify audit integrity"}, status=403)

    # Gate: admin must have some existing relationship with this
    # patient through their own hospital before verifying at all --
    # otherwise any admin could probe any patient's NHID
    has_relationship = AuditLog.objects.filter(patient=patient, hospital=request.user.hospital).exists()
    if not has_relationship:
        return Response(
            {"status": "error", "code": "NOT_FOUND",
             "message": "No activity for this patient at your hospital."},
            status=404
        )

    # The integrity check itself still verifies the FULL chain
    # (across all hospitals) -- this is a hash chain requirement,
    # not a scoping choice. See explanation above.
    is_valid, broken_at_id = verify_chain_integrity(patient=patient)

    return Response({
        "status": "success",
        "message": "Chain intact" if is_valid else "Tampering detected",
        "data": {"is_valid": is_valid, "broken_at_entry_id": broken_at_id},
    })