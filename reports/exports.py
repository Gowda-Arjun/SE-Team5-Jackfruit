"""CSV and PDF export of a report (HMS-F-041). Both render the exact report dict shown on screen."""
import csv
import datetime
import io

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _filename(report, ext):
    slug = report["title"].lower().replace(" ", "-")
    return f"hms-{slug}-{datetime.date.today():%Y%m%d}.{ext}"


def _all_rows(report):
    rows = [report["columns"], *report["rows"]]
    if report.get("totals"):
        rows.append(report["totals"])
    return [[str(cell) for cell in row] for row in rows]


def to_csv(report):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{_filename(report, "csv")}"'
    response.write("\ufeff")  # BOM so Excel opens UTF-8 correctly
    writer = csv.writer(response)
    writer.writerow([report["title"]])
    writer.writerow([report["note"]])
    writer.writerows(_all_rows(report))
    return response


def render_pdf(report, compress=True):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), title=report["title"], author="HMS",
                            pageCompression=1 if compress else 0)
    styles = getSampleStyleSheet()
    table = Table(_all_rows(report), repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#212529")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ]
    if report.get("totals"):
        style.append(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))
    table.setStyle(TableStyle(style))
    doc.build([
        Paragraph(f"Hostel Management System - {report['title']}", styles["Title"]),
        Paragraph(report["note"], styles["Normal"]),
        Paragraph(f"Generated {datetime.datetime.now():%d %b %Y %H:%M}", styles["Normal"]),
        Spacer(1, 12),
        table,
    ])
    return buffer.getvalue()


def to_pdf(report):
    response = HttpResponse(render_pdf(report), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{_filename(report, "pdf")}"'
    return response
