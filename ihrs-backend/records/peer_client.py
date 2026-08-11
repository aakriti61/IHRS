import requests
import logging

from accounts.models import PeerHospital, Patient

logger = logging.getLogger(__name__)


def broadcast_lookup(nhid, on_behalf_of, justification=None, requested_by=None):
    """
    Broadcasts a patient lookup request to every configured PeerHospital.
    Returns a list of dicts, one per peer that responded with something
    useful -- peers with no record of this nhid are simply skipped.
    """
    peers = PeerHospital.objects.all()
    results = []

    for peer in peers:
        try:
            url = f"{peer.base_url.rstrip('/')}/api/records/external/lookup/{nhid}/"
            headers = {
                "X-Hospital-Key": peer.shared_secret,
                "Content-Type": "application/json",
            }
            params = {"on_behalf_of": on_behalf_of}
            if justification:
                params["justification"] = justification
            if requested_by:
                params["requested_by"] = requested_by

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if not data.get("data", {}).get("found", True):
                    continue
                payload = data.get("data", data)
                results.append({
                    "peer_name": peer.name,
                    "demographics": payload.get("demographics", {}),
                    "records": payload.get("records", []),
                    "consent_required": payload.get("consent_required", False),
                })
            else:
                logger.warning(f"Peer {peer.name} returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to contact peer {peer.name}: {str(e)}")
            continue

    return results


def get_or_cache_patient(nhid):
    """
    Returns the local Patient if we already have one, otherwise asks
    every peer for demographics and caches a local Patient row from
    the first peer that has them.

    Returns None (never raises) when nobody -- local or any peer --
    has heard of this nhid, so callers can do a plain `if not patient`
    check and return their own 404 response.
    """
    try:
        return Patient.objects.get(nhid=nhid)
    except Patient.DoesNotExist:
        pass

    peer_results = broadcast_lookup(nhid, on_behalf_of="doctor")

    demographics = next(
        (p["demographics"] for p in peer_results if p.get("demographics")),
        None,
    )
    if not demographics:
        return None

    return Patient.objects.create(
        nhid=nhid,
        full_name=demographics.get("full_name", ""),
        dob=demographics.get("dob"),
        blood_group=demographics.get("blood_group", ""),
        phone=demographics.get("phone", ""),
        emergency_contact=demographics.get("emergency_contact", ""),
    )


def merge_peer_records(peer_results):
    """
    Flattens records (and their nested lab_reports) from multiple
    peers into two combined lists: (all_records, all_lab_reports).
    """
    all_records = []
    all_lab_reports = []

    for result in peer_results:
        records = result.get("records", [])
        all_records.extend(records)
        for rec in records:
            all_lab_reports.extend(rec.get("lab_reports", []))

    return all_records, all_lab_reports


def broadcast_consent_event(nhid, hospital_name, granted):
    """
    Notifies the named peer hospital that a patient granted or revoked
    consent to it. Fire-and-forget: a failed sync here doesn't roll
    back the consent change itself, just gets logged for follow-up.
    """
    peers = PeerHospital.objects.filter(name=hospital_name)

    for peer in peers:
        try:
            url = f"{peer.base_url.rstrip('/')}/api/consent/peer/consent/sync/"
            headers = {
                "X-Hospital-Key": peer.shared_secret,
                "Content-Type": "application/json",
            }
            response = requests.post(
                url,
                json={"nhid": nhid, "hospital_name": hospital_name, "granted": granted},
                headers=headers,
                timeout=10,
            )
            if response.status_code not in (200, 201):
                logger.warning(f"Consent sync to {peer.name} failed with {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Consent sync failed for {peer.name}: {str(e)}")