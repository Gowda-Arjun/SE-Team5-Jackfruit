"""HMS URL configuration.

Every feature module is already wired in here, so feature PRs only touch
their own app's urls.py (fewer merge conflicts).
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("allocation/", include("allocation.urls")),
    path("fees/", include("fees.urls")),
    path("complaints/", include("complaints.urls")),
    path("reports/", include("reports.urls")),
]
