# audit/urls.py

from django.urls import path
from audit.views import audit_logs_view, verify_audit_chain_view

urlpatterns = [
    path("logs/<str:nhid>/", audit_logs_view, name="audit-logs"),
    path("verify/<str:nhid>/", verify_audit_chain_view, name="audit-verify"),
]