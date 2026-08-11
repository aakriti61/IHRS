from django.contrib import admin, messages
from .models import CustomUser, Hospital, Patient ,SiteContact, PeerHospital
from .views import generate_temp_password


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("phone", "full_name", "role", "hospital", "is_active")
    exclude = ("password",)

    def save_model(self, request, obj, form, change):
        if not change:
            temp_password = generate_temp_password()
            obj.set_password(temp_password)
            obj.must_change_password = True
            super().save_model(request, obj, form, change)
            # Django admin ko "success" banner मा password देखाउने --
            # यही एकमात्र ठाउँ हो जहाँ यो plaintext मा देखिन्छ, save
            # भएपछि फेरि कहिल्यै फर्किंदैन (HealthRecord जस्तै hash
            # भइसकेपछि DB मा plaintext रहँदैन)
            messages.warning(
                request,
                f"Temporary password for {obj.full_name}: {temp_password} "
                f"-- copy this now, it will not be shown again."
            )
        else:
            super().save_model(request, obj, form, change)


class HospitalAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "license_number")


class PeerHospitalAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "base_url", "created_at")


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Hospital, HospitalAdmin)
admin.site.register(Patient)
admin.site.register(SiteContact)
admin.site.register(PeerHospital, PeerHospitalAdmin)