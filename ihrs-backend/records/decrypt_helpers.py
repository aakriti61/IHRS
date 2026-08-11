"""
Shared decrypt/filter/score logic, used by BOTH:
  - read_record_view (local patient/doctor viewing this hospital's own DB)
  - external_views.external_lookup_view (a PEER hospital asking this
    hospital, over the network, for whatever it has on an NHID)

Pulling this into one place is deliberate: we already hit a real bug
once in this project (accounts/views.py vs accounts/staff_views.py had
two copies of create_staff_view that silently drifted apart). Writing
the decrypt/filter/risk-score/lifestyle logic ONCE here and having both
call sites use it means there is only one place to get it right, and
one place to fix if something's wrong -- not two that can go out of sync.
"""
import json as json_lib
from crypto.rsa import rsa_decrypt
from crypto.aes import aes_decrypt
from .clinical_scores import calculate_news2
from .lifestyle_engine import build_lifestyle_summary

# "Medico" = clinical roles who may see the NEWS2 risk score and
# confidential_notes. hospital_admin/receptionist are deliberately
# EXCLUDED -- neither is a treating clinician, so they get the same
# patient-safe view as everyone else non-clinical.
MEDICO_ROLES = {"doctor", "nurse"}


def decrypt_patient_records(patient, is_medico):
    """
    Decrypts every HealthRecord (and its LabReports) for this patient,
    applies the same visibility rules everywhere in the app:
      - confidential_notes and risk_score only ever attached if
        is_medico is True -- never for a patient, never for a peer
        hospital's own patient-facing broadcast.
      - lifestyle_summary is built from ALL lab reports found, and is
        ALWAYS included regardless of is_medico (it's meant for the
        patient, medico viewers can see it too but it's never hidden
        from either).

    Returns: (decrypted_records: list[dict], lifestyle_summary: dict)
    """
    decrypted_records = []
    all_lab_reports_flat = []

    for record in patient.health_records.all():
        private_key = record.hospital.get_private_key_tuple()
        aes_key = rsa_decrypt(bytes(record.aes_key_encrypted), private_key)
        data_bytes = aes_decrypt(bytes(record.encrypted_data), aes_key)
        record_data = json_lib.loads(data_bytes.decode("utf-8"))

        lab_reports = []
        for lab in record.lab_reports.all():
            lab_aes_key = rsa_decrypt(bytes(lab.aes_key_encrypted), private_key)
            lab_bytes = aes_decrypt(bytes(lab.encrypted_data), lab_aes_key)
            lab_entry = {
                "id": lab.id,
                "added_by": lab.added_by.full_name if lab.added_by else "N/A",
                "created_at": lab.created_at,
                **json_lib.loads(lab_bytes.decode("utf-8")),
            }
            lab_reports.append(lab_entry)
            all_lab_reports_flat.append(lab_entry)

        risk_score = None
        if is_medico:
            risk_score = calculate_news2(record_data.get("vitals", {}))
        else:
            record_data = {
                k: v for k, v in record_data.items() if k != "confidential_notes"
            }

        record_entry = {
            "record_id": record.id,
            "hospital": record.hospital.name,
            "hospital_id": record.hospital_id,
            "doctor": record.doctor.full_name if record.doctor else "N/A",
            "visit_type": record.visit_type,
            "created_at": record.created_at,
            "data": record_data,
            "lab_reports": lab_reports,
        }
        if is_medico:
            record_entry["risk_score"] = risk_score

        decrypted_records.append(record_entry)

    lifestyle_summary = build_lifestyle_summary(all_lab_reports_flat)
    return decrypted_records, lifestyle_summary