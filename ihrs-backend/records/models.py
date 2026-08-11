from django.db import models
from accounts.models import Patient, Hospital, CustomUser


class HealthRecord(models.Model):
    VISIT_TYPE_CHOICES = [
        ("emergency", "Emergency"),
        ("followup", "Follow-up"),
        ("routine", "Routine"),
    ]

    # Kasko record ho — Patient model sanga direct FK.
    # on_delete=PROTECT: patient delete hunda uska medical
    # records galti le pani delete huna hudaina — legal/medical
    # record ho, accidentally lose garna mildaina.
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="health_records"
    )

    # Kun hospital ma banayeko — decrypt garda yehi hospital ko
    # RSA private_key chahincha (aes_key_encrypted decrypt garna).
    hospital = models.ForeignKey(
        Hospital, on_delete=models.PROTECT, related_name="health_records"
    )

    # Kun doctor le create garyo — audit trail ko lagi.
    # SET_NULL किन? Doctor ko account delete/deactivate bhaye pani
    # record aaphai (medical history) survive hunuparxa — record
    # loss huna hudaina, doctor reference matra null hunxa.
    doctor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True,
        related_name="created_records"
    )

    visit_type = models.CharField(max_length=20, choices=VISIT_TYPE_CHOICES)

    # AES-CBC encrypted JSON blob — aes.py ko aes_encrypt() le
    # return garne raw bytes (IV + ciphertext) direct store huncha.
    encrypted_data = models.BinaryField()

    # AES key (16 bytes), hospital ko RSA public_key le encrypted.
    # rsa.py ko rsa_encrypt() ko output — yo store nagarikan
    # encrypted_data lai decrypt garne cabi (AES key) nै haraucha.
    aes_key_encrypted = models.BinaryField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # naya record pahila deखिने — dashboard/history view ko lagi natural

    def __str__(self):
        return f"Record for {self.patient.nhid} — {self.visit_type} ({self.created_at.date()})"


class LabReport(models.Model):
    # Kun visit/record sanga related cha -- HealthRecord decrypt hune
    # tehi hospital ko key le yo pani decrypt huncha, tesले garda
    # arू model/key chahiदैन, existing pattern reuse huncha
    record = models.ForeignKey(
        HealthRecord, on_delete=models.PROTECT, related_name="lab_reports"
    )

    # Kun nurse/doctor le थپ्यो -- audit ko lagi, record ko doctor
    # field jastai SET_NULL (account delete भए पनि report survive होस्)
    added_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True,
        related_name="lab_reports_added"
    )

    # HealthRecord jastai hybrid encryption -- fresh AES key, hospital
    # ko RSA public key le wrap
    encrypted_data = models.BinaryField()
    aes_key_encrypted = models.BinaryField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Lab report on record #{self.record_id} by {self.added_by}"