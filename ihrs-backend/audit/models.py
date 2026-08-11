# audit/models.py

from django.db import models
from accounts.models import CustomUser, Patient, Hospital


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("RECORD_CREATED", "Record Created"),
        ("RECORD_VIEWED", "Record Viewed"),
        ("CONSENT_GRANTED", "Consent Granted"),
        ("CONSENT_REVOKED", "Consent Revoked"),
        ("EMERGENCY_ACCESS_GRANTED", "Emergency Access Granted"),
        ("LAB_REPORT_ADDED","Lab Report Added")
    ]

    # Who performed the action. SET_NULL (not PROTECT) because an
    # audit log entry must survive even if the actor's account is
    # later deleted — the log is the permanent record, the user
    # reference is secondary information.
    actor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True,
        related_name="audit_entries"
    )

    action = models.CharField(max_length=30, choices=ACTION_CHOICES)

    # Which patient's data this action relates to.
    # PROTECT: an audit trail must never silently lose entries
    # just because the patient row was deleted.
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="audit_entries"
    )

    # nullable: a cross-hospital consent grant (e.g. this hospital's
    # patient granting access to peer "TUTH") has no LOCAL Hospital row
    # to point at -- hospital_name captures the name either way, and
    # hospital is filled in only when a real local row exists, same
    # "identify by name when no local row exists" pattern used by
    # AccessConsent.hospital_name.
    hospital = models.ForeignKey(
        Hospital, on_delete=models.PROTECT, related_name="audit_entries",
        null=True, blank=True,
    )
    hospital_name = models.CharField(max_length=255, blank=True)
    # Only populated for a CROSS-hospital emergency bypass (no local
    # EmergencyAccessRequest exists at the RELEASING hospital, since
    # the requesting doctor isn't a user in this database at all) --
    # this is the only record of who asked and why, so it matters more
    # here than anywhere else in the audit log.
    justification = models.TextField(blank=True)

    timestamp = models.DateTimeField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # The two hash-chain fields — this is what makes tampering detectable.
    prev_hash = models.CharField(max_length=64)
    hash = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["id"]  # chain order must match insertion order, never reordered

    def __str__(self):
        return f"[{self.timestamp}] {self.action} — {self.patient.nhid} (by {self.actor})"