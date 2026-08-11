"""
records/external_views.py

RECEIVER side of hospital-to-hospital lookups -- the counterpart to
records/peer_client.py's broadcast_lookup(), which is the CALLER side.
This is what runs when a PEER hospital's server asks THIS hospital
"do you have anything for this NHID?" over HTTP.

BUG FIX (see chat): this file used to NOT define external_lookup_view
at all -- it contained stale, unused copies of the emergency-access
review functions instead (those live for real in
access_control/emergency_views.py). Since records/urls.py does
`from .external_views import external_lookup_view`, that name not
existing here raised an ImportError the moment Django loaded
records/urls.py, which broke EVERY endpoint in the records app
(create/, read/search, add-lab-report) -- not just cross-hospital
lookups.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from accounts.models import Patient, PeerHospital
from access_control.models import AccessConsent
from audit.hash_chain import create_log_entry
from .decrypt_helpers import decrypt_patient_records

# Callers that bypass this hospital's own consent check entirely:
#   "patient"   -- the patient viewing their own history, no consent needed.
#   "emergency" -- break-glass override, already justified at the
#                  calling hospital; still logged here with the reason.
# Anything else ("doctor") is subject to whatever AccessConsent this
# hospital's patient has (or hasn't) granted to the calling peer.
CONSENT_BYPASS_REASONS = {"patient", "emergency"}


@api_view(["GET"])
@permission_classes([AllowAny])  # no logged-in user on either end of a hospital-to-hospital call
def external_lookup_view(request, nhid):
    """
    Called BY a peer hospital's server (never directly by a browser).
    Auth is the X-Hospital-Key header matched against a local
    PeerHospital row -- see PeerHospital's docstring in accounts/models.py.
    """
    shared_key = request.headers.get("X-Hospital-Key")
    peer = PeerHospital.objects.filter(shared_secret=shared_key).first() if shared_key else None
    if not peer:
        return Response(
            {"status": "error", "code": "FORBIDDEN",
             "message": "Unknown or missing hospital key."},
            status=status.HTTP_403_FORBIDDEN,
        )

    on_behalf_of = request.GET.get("on_behalf_of", "doctor")
    justification = request.GET.get("justification", "")
    requested_by = request.GET.get("requested_by", "")

    try:
        patient = Patient.objects.get(nhid=nhid)
    except Patient.DoesNotExist:
        # Genuinely unknown here -- NOT an error, just "found: False"
        # so the calling hospital can keep asking its other peers.
        return Response({"status": "success", "message": "Not found here.",
                          "data": {"found": False}})

    # Demographics travel regardless of consent -- same as showing a
    # physical ID card. Clinical records are what consent actually gates.
    demographics = {
        "full_name": patient.full_name,
        "dob": patient.dob,
        "blood_group": patient.blood_group,
        "phone": patient.phone,
        "emergency_contact": patient.emergency_contact,
    }

    bypasses_consent = on_behalf_of in CONSENT_BYPASS_REASONS
    consent = None
    if not bypasses_consent:
        consent = AccessConsent.objects.filter(
            patient=patient, hospital_name=peer.name
        ).first()
    has_consent = bypasses_consent or bool(consent and consent.is_valid())

    # Always log this on OUR OWN audit trail: our patient's data is
    # being looked at by someone at another hospital. actor is None --
    # the requesting doctor isn't a user in THIS database at all --
    # so requested_by is folded into the justification text instead,
    # otherwise that name would be lost entirely.
    log_justification = f"[{requested_by}] {justification}".strip() if requested_by else justification
    create_log_entry(
        actor=None,
        action="EMERGENCY_ACCESS_GRANTED" if on_behalf_of == "emergency" else "RECORD_VIEWED",
        patient=patient,
        hospital=None,
        hospital_name=peer.name,
        justification=log_justification,
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    if not has_consent:
        return Response({
            "status": "success",
            "message": "Consent required.",
            "data": {
                "found": True,
                "consent_required": True,
                "demographics": demographics,
                "records": [],
            },
        })

    is_medico = on_behalf_of in ("doctor", "nurse", "emergency")
    decrypted_records, lifestyle_summary = decrypt_patient_records(patient, is_medico)

    return Response({
        "status": "success",
        "message": f"{len(decrypted_records)} record(s) found.",
        "data": {
            "found": True,
            "consent_required": False,
            "demographics": demographics,
            "records": decrypted_records,
            "lifestyle_summary": lifestyle_summary,
        },
    })