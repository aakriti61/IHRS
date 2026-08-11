from rest_framework import serializers


class VitalsSerializer(serializers.Serializer):
    """
    Structured vitals -- required for NEWS2 scoring (see clinical_scores.py)
    to mean anything. All fields optional here at the input level (not
    every visit captures every vital -- e.g. a phone follow-up), but
    calculate_news2() treats a missing value as contributing 0 to the
    score rather than raising an error, and this is visible in its
    breakdown output so the score stays auditable, not a black box.

    NOTE: vitals themselves (BP, pulse, temp) are ordinary clinical
    data a patient is entitled to see -- it's the COMPUTED RISK SCORE
    derived from them that must stay medico-only, not the raw numbers.
    That filtering happens in read_record_view, not here.
    """
    respiratory_rate = serializers.IntegerField(required=False, allow_null=True)
    spo2 = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=100)
    on_oxygen = serializers.BooleanField(required=False, default=False)
    systolic_bp = serializers.IntegerField(required=False, allow_null=True)
    pulse = serializers.IntegerField(required=False, allow_null=True)
    consciousness = serializers.ChoiceField(
        choices=["A", "C", "V", "P", "U"],  # ACVPU scale
        required=False, default="A"
    )
    temperature = serializers.FloatField(required=False, allow_null=True)


class CreateRecordSerializer(serializers.Serializer):
    """
    Doctor le record banauda pathaune input validate garne.
    ModelSerializer hoina किनकि HealthRecord model ma directly
    save huне fields (encrypted_data, aes_key_encrypted) yaha
    hunuhudaina — ती chai view le compute garcha, user le dinu hudaina.

    record_data (jun encrypt huन्छ) ko structure aba EXPLICIT cha
    (pahिले free JSONField thiyo -- flexible tara unstructured,
    confidential vs patient-visible chuttyaउन sakiदैनthyo):

    - diagnosis, prescription, notes -> patient le pani herna paune
    - confidential_notes -> DOCTOR/NURSE matra herna paune, patient lai
      kahilyai response ma deखाउँdaina (read_record_view le filter garcha)
    - vitals -> NEWS2 score nikालna structured numbers चाहिन्छ
    """
    patient_nhid = serializers.CharField(max_length=20)
    visit_type = serializers.ChoiceField(
        choices=["emergency", "followup", "routine"]
    )
    diagnosis = serializers.CharField(allow_blank=True, required=False, default="")
    prescription = serializers.CharField(allow_blank=True, required=False, default="")
    notes = serializers.CharField(allow_blank=True, required=False, default="")
    confidential_notes = serializers.CharField(allow_blank=True, required=False, default="")
    vitals = VitalsSerializer(required=False, default=dict)

    def validate(self, data):
        # Yehi dict chai json.dumps() bhaera encrypt huncha (views.py
        # ma validated["record_data"] use huncha) -- view code
        # yesपछि change garनु pardैन, structure yahाँ matra tयार garincha.
        data["record_data"] = {
            "diagnosis": data.get("diagnosis", ""),
            "prescription": data.get("prescription", ""),
            "notes": data.get("notes", ""),
            "confidential_notes": data.get("confidential_notes", ""),
            "vitals": data.get("vitals", {}),
        }
        return data


class AddLabReportSerializer(serializers.Serializer):
    """
    PAHILE: test_name (free text) + result (free text CharField) --
    "145 mg/dL" ra "7.2 mmol/L" jasto free-text string ma numeric
    trend analysis GARNA MILDAINA (parsing fragile huncha).

    ABA: test_type euta FIXED choice bata, value euta REAL number,
    unit chai test_type bata auto-derive huncha (user le type gardaina,
    so "mg/dL" vs "mgdl" jasto inconsistency aaudaina). Yesले
    lifestyle_engine.py ko trend analysis lai reliable banaucha.
    """
    LAB_TEST_CHOICES = [
        ("glucose_fasting", "Fasting Blood Glucose"),
        ("hba1c", "HbA1c"),
        ("creatinine", "Serum Creatinine"),
        ("hemoglobin", "Hemoglobin"),
        ("systolic_bp", "Systolic Blood Pressure (lab-recorded)"),
        ("ldl_cholesterol", "LDL Cholesterol"),
        ("bmi", "Body Mass Index"),
    ]

    UNIT_MAP = {
        "glucose_fasting": "mg/dL",
        "hba1c": "%",
        "creatinine": "mg/dL",
        "hemoglobin": "g/dL",
        "systolic_bp": "mmHg",
        "ldl_cholesterol": "mg/dL",
        "bmi": "kg/m2",
    }

    test_type = serializers.ChoiceField(choices=LAB_TEST_CHOICES)
    value = serializers.FloatField()
    remarks = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        data["unit"] = self.UNIT_MAP[data["test_type"]]
        return data