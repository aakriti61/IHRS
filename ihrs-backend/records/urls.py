from django.urls import path
from .views import create_record_view , read_record_view , add_lab_report_view
from .external_views import external_lookup_view

urlpatterns = [
    path("create/", create_record_view, name="create_record"),
    path("external/lookup/<str:nhid>/", external_lookup_view, name="external-lookup"),
    path("<str:nhid>/", read_record_view, name="read_record"),
    path("<int:record_id>/lab-report/", add_lab_report_view, name="add-lab-report"),
]