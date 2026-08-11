# access_control/models.py

import secrets
from django.db import models
from django.utils import timezone
from accounts.models import Patient


class AccessConsent(models.Model):
    """
    hospital is identified by NAME (string), not a ForeignKey to a
    local Hospital row. Why: this table needs to record consent for
    BOTH this hospital's own local doctors AND for a completely
    separate peer hospital (e.g. Bir's database recording that the
    patient consented to "TUTH") -- and TUTH's real Hospital row lives
    only in TUTH's OWN separate database, never in this one. Using a
    plain name string sidesteps needing a fake placeholder row just to
    satisfy a foreign key.
    """
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="consents"
    )
    hospital_name = models.CharField(max_length=255)

    granted = models.BooleanField(default=True)

    # secrets.token_hex(32) le 64-character hex string banaucha —
    # random.random() jasto predictable hoina, cryptographically
    # secure random (secure sharing link ko lagi essential)
    token = models.CharField(max_length=64, unique=True, editable=False)

    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        # euta patient le euta hospital lai euटै time ma
        # DUITA active consent dिन नमिलोस (data consistency)
        unique_together = ("patient", "hospital_name")

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Consent granted cha ra expire vaisakeko chaina bhane True"""
        return self.granted and timezone.now() < self.expires_at

    def __str__(self):
        status = "ACTIVE" if self.is_valid() else "EXPIRED/REVOKED"
        return f"{self.patient.nhid} -> {self.hospital_name} [{status}]"