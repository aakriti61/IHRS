from datetime import timedelta
from django.db import models
from django.utils import timezone
from accounts.models import Patient, CustomUser


class EmergencyAccessRequest(models.Model):
    doctor = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT, related_name="emergency_requests"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="emergency_requests"
    )

    # Compulsory reason for bypassing consent — this is the
    # accountability anchor. Minimum length enforced in the view
    # (not here) so we can return a clear validation error message.
    justification = models.TextField()

    requested_at = models.DateTimeField(auto_now_add=True)

    # Fixed 1-hour window — set once at creation, never extended.
    # A doctor needing more time must file a new request (new
    # justification, new audit trail entry) rather than silently
    # keep an old one alive.
    expires_at = models.DateTimeField()

    # Flips to True once a hospital_admin has looked at this request.
    # Does not block access — review happens after the fact, by design.
    reviewed_by_admin = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def is_active(self):
        """True while the 1-hour emergency window has not yet expired."""
        return timezone.now() < self.expires_at

    def __str__(self):
        status = "ACTIVE" if self.is_active() else "EXPIRED"
        reviewed = "reviewed" if self.reviewed_by_admin else "pending review"
        return f"{self.doctor} -> {self.patient.nhid} [{status}, {reviewed}]"