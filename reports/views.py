from django.shortcuts import render

from accounts.models import User
from core.decorators import role_required

from .exports import to_csv, to_pdf
from .forms import ReportForm
from .services import ReportUnavailable, build_report

EXPORTERS = {"csv": to_csv, "pdf": to_pdf}


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def report_view(request):
    """Occupancy, vacancy, fee-collection and defaulter reports for a date range (HMS-F-040),
    exportable as CSV or PDF with the same data as the screen (HMS-F-041)."""
    form = ReportForm(request.GET or None)
    report, error = None, None
    if form.is_bound and form.is_valid():
        d = form.cleaned_data
        try:
            report = build_report(d["type"], d["date_from"], d["date_to"])
        except ReportUnavailable as exc:
            error = str(exc)
        if report and request.GET.get("export") in EXPORTERS:
            return EXPORTERS[request.GET["export"]](report)
    status = 400 if form.is_bound and not form.is_valid() else 200
    return render(request, "reports/report.html", {"form": form, "report": report, "error": error}, status=status)
