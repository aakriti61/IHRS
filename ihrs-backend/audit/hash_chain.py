import hashlib

# The very first entry in the chain has no predecessor, so we use
# a fixed "genesis" value instead of leaving prev_hash empty.
# 64 zero characters, same length as a real SHA256 hex digest —
# keeps the field format consistent for the first row too.
GENESIS_HASH = "0" * 64


def compute_log_hash(prev_hash, actor_id, action, patient_id, timestamp):
    """
    Build the hash for one audit log entry.

    The hash depends on this entry's own data AND on the previous
    entry's hash. That second part is what creates the "chain" —
    changing any past entry changes its hash, which then no longer
    matches what the next entry expected as prev_hash.
    """
    payload = f"{prev_hash}|{actor_id}|{action}|{patient_id}|{timestamp.isoformat()}"
    return hashlib.sha256(payload.encode()).hexdigest()


def get_last_hash():
    """
    Fetch the hash of the most recent AuditLog entry, or the
    genesis hash if the table is still empty (first-ever log entry).
    """
    # Import inside the function to avoid circular imports between
    # audit/models.py and audit/hash_chain.py.
    from audit.models import AuditLog

    last_entry = AuditLog.objects.order_by("-id").first()
    return last_entry.hash if last_entry else GENESIS_HASH


def create_log_entry(actor, action, patient, hospital=None, hospital_name=None, justification="", ip_address=None):
    """
    Create and save a new AuditLog entry, correctly chained to
    whatever the current last entry is.

    hospital: a real local Hospital object, when one exists (the
    normal case -- record created/viewed at THIS hospital, or consent
    granted to a hospital that has a local row).
    hospital_name: always required in effect -- if hospital is given
    and hospital_name isn't, it's taken from hospital.name. Needed on
    its own for a cross-hospital consent grant, where the target
    hospital (e.g. peer "TUTH") has no local row to reference at all.
    """
    from audit.models import AuditLog
    from django.utils import timezone

    if hospital_name is None:
        hospital_name = hospital.name if hospital else ""

    prev_hash = get_last_hash()
    timestamp = timezone.now()

    entry_hash = compute_log_hash(
        prev_hash=prev_hash,
        actor_id=actor.id if actor else None,
        action=action,
        patient_id=patient.id,
        timestamp=timestamp,
    )

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        patient=patient,
        hospital=hospital,
        hospital_name=hospital_name,
        justification=justification,
        ip_address=ip_address,
        prev_hash=prev_hash,
        hash=entry_hash,
        timestamp=timestamp,
    )


def verify_chain_integrity(patient=None):
    """
    Walk the entire chain (or just one patient's entries) in order
    and recompute every hash. Returns (is_valid, broken_at_id).

    broken_at_id is the id of the first entry whose stored hash no
    longer matches what we recompute — that tells the admin exactly
    where tampering happened, not just "something is wrong".
    """
    from audit.models import AuditLog

    queryset = AuditLog.objects.order_by("id")
    if patient:
        queryset = queryset.filter(patient=patient)

    expected_prev_hash = GENESIS_HASH

    for entry in queryset:
        recomputed = compute_log_hash(
            prev_hash=expected_prev_hash,
            actor_id=entry.actor_id,
            action=entry.action,
            patient_id=entry.patient_id,
            timestamp=entry.timestamp,
        )

        if recomputed != entry.hash:
            return False, entry.id

        if entry.prev_hash != expected_prev_hash:
            return False, entry.id

        expected_prev_hash = entry.hash

    return True, None