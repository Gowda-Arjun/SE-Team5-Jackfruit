import csv
import datetime
import io

from django.urls import reverse

from reports.exports import render_pdf
from reports.services import build_report

from .conftest import TODAY

MONTH_AGO = TODAY - datetime.timedelta(days=31)
SAMPLE = {
    "title": "Occupancy by block",
    "columns": ["Block", "Beds", "Occupied"],
    "rows": [["Block A", 4, 2], ["Block B", 1, 1]],
    "totals": ["Total", 5, 3],
    "note": "Sample note",
}


def params(export):
    return {"type": "occupancy", "date_from": MONTH_AGO.isoformat(), "date_to": TODAY.isoformat(), "export": export}


def test_pdf_contains_every_row_and_total():
    pdf = render_pdf(SAMPLE, compress=False)
    assert pdf.startswith(b"%PDF")
    for text in (b"Occupancy by block", b"Block A", b"Block B", b"Total", b"Sample note"):
        assert text in pdf


def test_csv_export_matches_screen(admin_client, hostel):
    """TC-Rep-02 / AC-F-041: exported file matches the on-screen data."""
    resp = admin_client.get(reverse("reports:index"), params("csv"))
    assert resp["Content-Type"].startswith("text/csv")
    assert resp["Content-Disposition"].startswith("attachment") and ".csv" in resp["Content-Disposition"]
    lines = list(csv.reader(io.StringIO(resp.content.decode("utf-8-sig"))))
    report = build_report("occupancy", MONTH_AGO, TODAY)
    assert lines[2] == report["columns"]
    assert lines[3:3 + len(report["rows"])] == [[str(c) for c in row] for row in report["rows"]]
    assert lines[-1] == [str(c) for c in report["totals"]]


def test_pdf_export_is_downloadable(admin_client, hostel):
    resp = admin_client.get(reverse("reports:index"), params("pdf"))
    assert resp["Content-Type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF") and ".pdf" in resp["Content-Disposition"]


def test_export_buttons_shown_with_report(admin_client, hostel):
    page = admin_client.get(reverse("reports:index"), params("")).content.decode()
    assert "Export CSV" in page and "Export PDF" in page
