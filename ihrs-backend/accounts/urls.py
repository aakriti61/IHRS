from django.urls import path
from .views import register_view, login_view, logout_view, change_password_view , update_phone_view , site_contact_view
from .staff_views import create_staff_view

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("change-password/", change_password_view, name="change-password"),
    path("profile/update-phone/", update_phone_view, name="update-phone"),
    path("staff/create/", create_staff_view, name="create-staff"),
    path("contact/", site_contact_view, name="site-contact"),
]