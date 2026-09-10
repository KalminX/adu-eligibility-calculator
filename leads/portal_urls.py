"""
URL patterns for the custom Staff & Administrator Lead Management Portal.
"""

from django.urls import path
from . import portal_views

app_name = "portal"

urlpatterns = [
    path("", portal_views.portal_dashboard, name="dashboard"),
    path("login/", portal_views.portal_login, name="login"),
    path("logout/", portal_views.portal_logout, name="logout"),
    path("leads/<int:lead_id>/", portal_views.portal_lead_detail, name="lead_detail"),
    path("leads/<int:lead_id>/resend-email/", portal_views.portal_resend_email, name="resend_email"),
    path("leads/<int:lead_id>/resend-whatsapp/", portal_views.portal_resend_whatsapp, name="resend_whatsapp"),
    path("leads/<int:lead_id>/delete/", portal_views.portal_lead_delete, name="lead_delete"),
    path("export/", portal_views.portal_export_csv, name="export_csv"),
]
