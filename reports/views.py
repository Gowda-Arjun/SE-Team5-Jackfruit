from django.shortcuts import render

from accounts.models import User
from core.decorators import role_required

from .forms import ReportForm
from .services import ReportUnavailable, build_report


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def report_view(request):
    """Occupancy, vacancy, fee-collection and defaulter reports for a date range (HMS-F-040)."""
    form = ReportForm(request.GET or None)
    report, error = None, None
    if form.is_bound and form.is_valid():
        d = form.cleaned_data
        try:
            report = build_report(d["type"], d["date_from"], d["date_to"])
        except ReportUnavailable as exc:
            error = str(exc)
    status = 400 if form.is_bound and not form.is_valid() else 200
    return render(request, "reports/report.html", {"form": form, "report": report, "error": error}, status=status)
