from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render


@login_required
def home(request):
    """Role-aware landing page: student dashboard or warden/admin dashboard."""
    template = "core/student_dashboard.html" if request.user.is_student else "core/admin_dashboard.html"
    return render(request, template)


def healthz(request):
    """Lightweight health check for uptime monitoring (HMS-NF-002)."""
    return JsonResponse({"status": "ok"})
