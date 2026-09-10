"""
URL configuration for ADU Eligibility Calculator.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#2563eb">'
    '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
    '<polyline points="9 22 9 12 15 12 15 22"/>'
    '</svg>'
)


def favicon_view(request):
    """Serves inline SVG favicon to prevent 404 errors in browser logs."""
    return HttpResponse(FAVICON_SVG, content_type="image/svg+xml")


urlpatterns = [
    path("favicon.ico", favicon_view, name="favicon"),
    path("admin/", admin.site.urls),
    path("portal/", include("leads.portal_urls")),
    path("", include("calculator.urls")),
    path("calculator/", include("leads.urls")),
]
