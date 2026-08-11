from django.urls import path
from .consent_views import grant_consent_view, revoke_consent_view

from access_control.emergency_views import (
    emergency_access_request_view,
    pending_emergency_reviews_view,
    mark_emergency_reviewed_view,
)
from .peer_consent_views import sync_consent



urlpatterns = [
    path("grant/", grant_consent_view, name="grant_consent"),
    path("revoke/", revoke_consent_view, name="revoke_consent"),
     path("emergency/request/<str:nhid>/", emergency_access_request_view, name="emergency-request"),
    path("emergency/pending/", pending_emergency_reviews_view, name="emergency-pending"),
    path("emergency/review/<int:request_id>/", mark_emergency_reviewed_view, name="emergency-review"),
    path("peer/consent/sync/",sync_consent ,name="sync-consent"),
]

