from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Hospital, Patient

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Register garda user le pathaune data validate garne.
    password chai write_only — kina? response ma password kahilepani
    fircera aaunu hudaina, security risk huncha.
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "id", "phone", "email", "full_name",
            "role", "hospital", "password",
        ]

    def validate_role(self, value):
        # patient role bata directly register huna dine hoina —
        # patient chai hospital le register garcha (Patient model separate cha)
        # yo business rule ho, tapaiko system design anusar adjust garna sakincha
        allowed_roles = ["patient", "doctor", "nurse", "hospital_admin", "receptionist"]
        if value not in allowed_roles:
            raise serializers.ValidationError(
                f"Invalid role. Allowed: {allowed_roles}"
            )
        return value

    def validate(self, data):
        # doctor/nurse/hospital_admin/receptionist ko hospital field compulsory hunuparcha
        role = data.get("role")
        hospital = data.get("hospital")

        if role in ["doctor", "nurse", "hospital_admin", "receptionist"] and not hospital:
            raise serializers.ValidationError(
                {"hospital": "Hospital is compulsary for this role."}
            )
        return data

    def create(self, validated_data):
        # CustomUserManager.create_user() use garcha — password automatically
        # hash huncha (set_password internally call huncha)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """
    ModelSerializer hoina — kina? login ma database ma naya record
    banaudaina, matra existing data validate garcha. Tesैले plain
    Serializer use garne, ModelSerializer hoina.
    """
    identifier = serializers.CharField()  # phone VA email, jun pani
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    nhid = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ["id", "phone", "email", "full_name", "role", "hospital", "nhid"]
    def get_nhid(self, obj):
        if obj.role == "patient" and obj.patient_profile:
            return obj.patient_profile.nhid
        return None