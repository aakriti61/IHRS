from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """
    AbstractBaseUser use garda Django le create_user/create_superuser
    afai dindaina — afai banaunu parcha. Yo manager le password
    hashing (set_password) handle garcha, natra plain text ma
    password DB ma save huncha — security risk.
    """

    def create_user(self, phone, full_name, role, email=None, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is necessary.")
        if not role:
            raise ValueError("Role needed (doctor/nurse/patient/hospital_admin)")

        if email:
            email = self.normalize_email(email)

        user = self.model(phone=phone, email=email, full_name=full_name, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "hospital_admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser.")

        return self.create_user(phone, full_name, password=password, **extra_fields)


class Hospital(models.Model):
    name = models.CharField(max_length=255)
    license_number = models.CharField(max_length=100, unique=True)
    city = models.CharField(max_length=100)

    # RSA keypair — hospital ko records encrypt/decrypt garna use huncha
    # TextField किन? RSA key ठूलो PEM/integer string हुन्छ, CharField ko
    # max_length limit ma sohaudaina
    public_key = models.TextField()
    private_key = models.TextField()  # production ma encrypt garera rakhnu parne,
                                       # viva-level project ma plain — trade-off note garne

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def get_public_key_tuple(self):
        """Returns (e, n) as integers, ready for rsa_encrypt()"""
        import json
        e, n = json.loads(self.public_key)
        return (e, n)

    def get_private_key_tuple(self):
        """Returns (d, n) as integers, ready for rsa_decrypt()"""
        import json
        d, n = json.loads(self.private_key)
        return (d, n)


class Patient(models.Model):
    BLOOD_GROUP_CHOICES = [
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
    ]

    nhid = models.CharField(max_length=20, unique=True)  # format: NH-00001-BIR
    full_name = models.CharField(max_length=255)
    dob = models.DateField()
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    # unique=True -- BUG FIX: CustomUser.phone was already unique, but
    # Patient.phone (a separate column, not a reference to
    # CustomUser.phone) had no constraint at all. In the normal
    # register_view flow this was masked because CustomUser.phone's
    # uniqueness check happens to catch the duplicate first -- but
    # anything that creates a Patient row directly (Django admin,
    # a script, a future endpoint) could silently create two Patient
    # rows sharing one phone number. Enforcing it here closes that gap
    # at the database level, not just in one code path.
    phone = models.CharField(max_length=15, unique=True)
    emergency_contact = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.nhid})"


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("doctor", "Doctor"),
        ("nurse", "Nurse"),
        ("patient", "Patient"),
        ("hospital_admin", "Hospital Admin"),
        ("receptionist", "Receptionist"),
    ]

    # phone PRIMARY identifier — Nepal ma sabaisanga email hudaina,
    # tara phone number lagbhag sabaisanga huncha
    phone = models.CharField(max_length=15, unique=True)

    # email OPTIONAL — institutional/professional use ko lagi
    email = models.EmailField(unique=True, null=True, blank=True)

    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    must_change_password = models.BooleanField(default=False)
    # nullable किन? patient role ko user ko hospital hudaina —
    # doctor/nurse/hospital_admin ko matra hunxa
    hospital = models.ForeignKey(
        Hospital, on_delete=models.SET_NULL, null=True, blank=True
    )

    # patient role ko user lai Patient record sanga link garna
    # (patient afai login garna chahanema useful)
    patient_profile = models.ForeignKey(
        Patient, on_delete=models.SET_NULL, null=True, blank=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Django admin access ko lagi

    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "phone"                  # login yehi field bata huncha
    REQUIRED_FIELDS = ["full_name", "role"]   # createsuperuser command le sodhcha

    def __str__(self):
        return f"{self.full_name} ({self.role})"
    
class SiteContact(models.Model):
    # Yo single-row model ho -- pura site ko lagi euta contact info matra
    # (per-hospital hoina, IHRS project/support contact)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return "Site contact info"


class PeerHospital(models.Model):
    """
    A small, LOCAL, mostly-static "address book" of other hospitals this
    server is allowed to exchange patient data with -- NOT a live
    registry service. Set up once per pair of hospitals (mirrors a real
    inter-hospital data-sharing agreement), not queried from anywhere
    external.

    shared_secret is used BOTH ways: this hospital sends it in the
    X-Hospital-Key header when CALLING that peer, and also checks
    incoming requests' X-Hospital-Key against the list of secrets
    stored here to confirm "this really is a hospital I trust" --
    NOT a per-user login token, since there's no logged-in user on
    either end of a hospital-to-hospital call.
    """
    name = models.CharField(max_length=255)
    base_url = models.URLField()  # e.g. http://localhost:8001
    shared_secret = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.base_url})"