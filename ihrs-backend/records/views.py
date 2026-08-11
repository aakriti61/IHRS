import json
import os

from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.models import Patient
from .models import HealthRecord
from .serializers import CreateRecordSerializer
from crypto.aes import aes_encrypt
from crypto.rsa import rsa_encrypt
from access_control.rbac import require_permission
from audit.hash_chain import create_log_entry
from .peer_client import broadcast_lookup, get_or_cache_patient

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@require_permission("create_record")
def create_record_view(request):
   
    # Doctor sanga hospital assigned hunuparxa (encryption ko lagi
    # hospital ko RSA key chahincha)
    if not request.user.hospital:
        return Response(
            {"status": "error", "code": "NO_HOSPITAL",
             "message": "Hospital not assigned with your account."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Step 2: input validate
    serializer = CreateRecordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"status": "error", "code": "INVALID_INPUT",
             "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    validated = serializer.validated_data

    # Step 3: patient fetch -- either already cached locally, or fetched
    # from a peer's demographics right now (see peer_client.py -- shared
    # with emergency_access_request_view so this logic lives in one place)
    patient = get_or_cache_patient(validated["patient_nhid"])
    if not patient:
        return Response(
            {"status": "error", "code": "PATIENT_NOT_FOUND",
             "message": "Patient with the NHID not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    hospital = request.user.hospital

    # Step 4: encryption flow
    # a) record data → JSON string → bytes
    data_bytes = json.dumps(validated["record_data"]).encode("utf-8")

    # b) naya random AES key — HAR record ko lagi FRESH key,
    #    kunai pani key reuse gardaina (euta leak bhaye arू sabai
    #    record safe rahos bhaneर)
    aes_key = os.urandom(16)

    # c) actual data AES le encrypt
    encrypted_data = aes_encrypt(data_bytes, aes_key)

    # d) AES key lai hospital ko RSA public key le encrypt
    #    (yehi encrypted key matra DB ma save huncha, plain
    #    AES key kahi pani store hudaina)
    public_key = hospital.get_public_key_tuple()
    aes_key_encrypted = rsa_encrypt(aes_key, public_key)

    # Step 5: save
    record = HealthRecord.objects.create(
        patient=patient,
        hospital=hospital,
        doctor=request.user,
        visit_type=validated["visit_type"],
        encrypted_data=encrypted_data,
        aes_key_encrypted=aes_key_encrypted,
    )


    create_log_entry(
    actor=request.user,
    action="RECORD_CREATED",
    patient=patient,
    hospital=hospital,
    ip_address=request.META.get("REMOTE_ADDR"),
    )  
    return Response(
        {"status": "success",
         "message": "Record succesfully encrypted and saved.",
         "data": {"record_id": record.id, "created_at": record.created_at}},
        status=status.HTTP_201_CREATED
    )

import json as json_lib
from access_control.models import AccessConsent
from access_control.emergency import EmergencyAccessRequest
from .decrypt_helpers import decrypt_patient_records, MEDICO_ROLES
from .peer_client import merge_peer_records
from .lifestyle_engine import build_lifestyle_summary
from datetime import datetime

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def read_record_view(request, nhid):

    patient = None
    local_patient = False

    # =====================================================
    # 1. FIRST SEARCH OWN DATABASE
    # =====================================================

    try:
        patient = Patient.objects.get(nhid=nhid)
        local_patient = True

    except Patient.DoesNotExist:
        local_patient = False


    local_records = []
    lifestyle_summary = None


    # =====================================================
    # 2. IF PATIENT EXISTS LOCALLY
    #    GET OWN HOSPITAL RECORDS
    # =====================================================

    if local_patient:

        is_self = (
            request.user.role == "patient"
            and request.user.patient_profile_id == patient.id
        )


        # Patient viewing own records
        if is_self:
            local_records, lifestyle_summary = decrypt_patient_records(
                patient,
                False
            )


        # Doctor/nurse from same hospital
        else:

            if not request.user.hospital:
                return Response(
                    {
                        "status": "error",
                        "message": "Hospital not assigned"
                    },
                    status=400
                )


            # Only decrypt records owned by this hospital
            # without needing consent
            local_records, lifestyle_summary = decrypt_patient_records(
                patient,
                True
            )



    # =====================================================
    # 3. ALWAYS SEARCH OTHER HOSPITALS
    # =====================================================


    active_emergency = None


    if request.user.role != "patient":

        active_emergency = (
            EmergencyAccessRequest.objects.filter(
                doctor=request.user,
                patient=patient,
                expires_at__gt=timezone.now()
            )
            .order_by("-requested_at")
            .first()
            if patient else None
        )


    if request.user.role == "patient":

        on_behalf_of = "patient"

    elif active_emergency:

        on_behalf_of = "emergency"

    else:

        on_behalf_of = request.user.role



    broadcast_kwargs = {}


    if active_emergency:

        broadcast_kwargs["justification"] = (
            active_emergency.justification
        )

        broadcast_kwargs["requested_by"] = (
            f"{request.user.full_name}"
        )



    peer_results = broadcast_lookup(
        nhid,
        on_behalf_of=on_behalf_of,
        **broadcast_kwargs
    )



    peer_records, peer_labs = merge_peer_records(peer_results)



    peers_requiring_consent = [
        p["peer_name"]
        for p in peer_results
        if p.get("consent_required")
    ]



    # =====================================================
    # 4. IF PATIENT DOES NOT EXIST LOCALLY
    #    CREATE BASIC INFO FROM PEER
    # =====================================================


    if not patient:

        demographics = next(
            (
                p["demographics"]
                for p in peer_results
                if p.get("demographics")
            ),
            {}
        )


        patient_info = {
            "nhid": nhid,
            **demographics
        }


    else:

        patient_info = {
            "nhid": patient.nhid,
            "full_name": patient.full_name,
            "phone": patient.phone,
            "dob": patient.dob,
            "blood_group": patient.blood_group,
            "emergency_contact": patient.emergency_contact,
        }



    # =====================================================
    # 5. DO NOT GIVE EXTERNAL RECORDS WITHOUT CONSENT
    # =====================================================


    allowed_peer_records = []


    for peer in peer_results:

        if peer.get("consent_required"):

            continue

        else:

            # FIX: each record here is JSON straight from the peer
            # hospital's own external_lookup_view response -- from
            # THEIR side these are just normal local records, so
            # nothing in the payload marks them as "peer" records.
            # We tag it here, on the receiving side, since only this
            # hospital knows the record arrived via broadcast rather
            # than from its own DB. The frontend (RecordCard.jsx) uses
            # this flag to hide "Add lab report" for peer records and
            # to label them "Fetched from {hospital}".
            for rec in peer.get("records", []):
                rec["is_peer_record"] = True
                allowed_peer_records.append(rec)



    # merge only allowed external records

    final_records = (
        local_records +
        allowed_peer_records
    )
    final_records = sorted(
        final_records,
        key=lambda x: str(x.get("created_at", "")),
        reverse=True
    )


    # =====================================================
    # 6. LIFESTYLE SUMMARY
    # =====================================================


    if final_records:

        all_labs = []

        for record in final_records:

            all_labs.extend(
                record.get("lab_reports", [])
            )


        lifestyle_summary = build_lifestyle_summary(
            all_labs
        )



    # =====================================================
    # 7. AUDIT LOG
    # =====================================================


    if request.user.role != "patient" and patient:

        create_log_entry(
            actor=request.user,
            action="RECORD_VIEWED",
            patient=patient,
            hospital=request.user.hospital,
            ip_address=request.META.get("REMOTE_ADDR"),
        )



    # =====================================================
    # 8. RESPONSE
    # =====================================================


    return Response(
        {
            "status": "success",

            "message":
                f"{len(final_records)} record(s) available",

            "data": {

                "patient": patient_info,

                "records": final_records,

                "lifestyle_summary":
                    lifestyle_summary,

                "peers_requiring_consent":
                    peers_requiring_consent,

                "external_hospitals": [
                    {
                        "hospital": p["peer_name"],
                        "has_records": bool(
                            p.get("records")
                        ),
                        "consent_required":
                            p.get(
                                "consent_required",
                                False
                            )
                    }

                    for p in peer_results

                    if p.get("records")
                    or p.get("demographics")
                ]
            }
        },

        status=status.HTTP_200_OK
    )
from .models import LabReport
from .serializers import AddLabReportSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@require_permission("add_lab_report")
def add_lab_report_view(request, record_id):
    try:
        record = HealthRecord.objects.get(id=record_id)
    except HealthRecord.DoesNotExist:
        return Response(
            {"status": "error", "code": "RECORD_NOT_FOUND",
             "message": "No record with this ID found."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Nurse/doctor le aफno hospital ले banayeko record मा matra lab
    # report थप्न पाउँछ -- arू hospital ko record मा touch गर्न मिल्दैन
    if record.hospital_id != request.user.hospital_id:
        return Response(
            {"status": "error", "code": "FORBIDDEN",
             "message": "You can only add lab reports to records from your own hospital."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = AddLabReportSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"status": "error", "code": "INVALID_INPUT", "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    data_bytes = json.dumps(serializer.validated_data).encode("utf-8")
    aes_key = os.urandom(16)
    encrypted_data = aes_encrypt(data_bytes, aes_key)

    public_key = record.hospital.get_public_key_tuple()
    aes_key_encrypted = rsa_encrypt(aes_key, public_key)

    lab_report = LabReport.objects.create(
        record=record,
        added_by=request.user,
        encrypted_data=encrypted_data,
        aes_key_encrypted=aes_key_encrypted,
    )

    create_log_entry(
        actor=request.user,
        action="LAB_REPORT_ADDED",
        patient=record.patient,
        hospital=record.hospital,
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    return Response(
        {"status": "success", "message": "Lab report added.",
         "data": {
             "lab_report_id": lab_report.id,
             "created_at": lab_report.created_at,
             "test_type": serializer.validated_data["test_type"],
             "value": serializer.validated_data["value"],
             "unit": serializer.validated_data["unit"],
         }},
        status=status.HTTP_201_CREATED
    )