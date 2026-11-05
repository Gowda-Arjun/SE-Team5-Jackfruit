"""Report data builders (HMS-F-040). Read-only; figures are computed in the database.

Every report returns the same structure, which the HTML page, CSV export and PDF export
all render, so an exported file always matches the screen (AC-F-041):

    {"title", "columns": [...], "rows": [[...], ...], "totals": [...] or None, "note": str}

The reports read other modules' models. Their names and fields are listed here in one place
(agreed in docs/guides/00_TEAM_WORKFLOW_read_first.md, section 6). If a module names
something differently, change it here only.
"""
import datetime

from django.apps import apps
from django.db.models import Count, F, Q, Sum

ROOM_MODEL = ("allocation", "Room")              # fields: block, number, capacity, occupancy, is_active
ALLOCATION_MODEL = ("allocation", "Allocation")  # fields: room, start_date, end_date
STATEMENT_MODEL = ("fees", "FeeStatement")       # fields: student, term, amount_due, amount_paid, due_date
PAYMENT_MODEL = ("fees", "Payment")              # fields: statement, amount, status, created_at
PAYMENT_SUCCESS = "SUCCESS"
PAYMENT_DATE_FIELD = "created_at"

REPORT_TYPES = {
    "occupancy": "Occupancy by block",
    "vacancy": "Vacant beds by room",
    "fee-collection": "Fee collection",
    "defaulters": "Fee defaulters",
}


class ReportUnavailable(Exception):
    """The module this report reads from has not been merged yet."""


def _model(spec, needed_by):
    try:
        return apps.get_model(*spec)
    except LookupError:
        raise ReportUnavailable(f"This report needs {spec[0]}.{spec[1]} ({needed_by}), which is not available yet.")


def build_report(report_type, date_from, date_to):
    builders = {
        "occupancy": occupancy_report,
        "vacancy": vacancy_report,
        "fee-collection": fee_collection_report,
        "defaulters": defaulters_report,
    }
    if report_type not in builders:
        raise ValueError(f"Unknown report type: {report_type}")
    if date_from > date_to:
        raise ValueError("The start date must be on or before the end date.")
    return builders[report_type](date_from, date_to)


def occupancy_report(date_from, date_to):
    """Beds per block and how many were occupied by allocations active at any time in the range."""
    Room = _model(ROOM_MODEL, "HMS-F-014")
    Allocation = _model(ALLOCATION_MODEL, "HMS-F-012")
    beds = {r["block__name"]: r for r in Room.objects.filter(is_active=True).values("block__name").annotate(
        rooms=Count("id"), beds=Sum("capacity"))}
    occupied = dict(
        Allocation.objects.filter(start_date__lte=date_to)
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=date_from))
        .values_list("room__block__name").annotate(n=Count("id")).values_list("room__block__name", "n")
    )
    rows = []
    for block in sorted(beds):
        total, used = beds[block]["beds"] or 0, occupied.get(block, 0)
        rows.append([block, beds[block]["rooms"], total, used, max(total - used, 0), _pct(used, total)])
    t_rooms, t_beds, t_used = (sum(r[i] for r in rows) for i in (1, 2, 3))
    return {
        "title": REPORT_TYPES["occupancy"],
        "columns": ["Block", "Rooms", "Beds", "Occupied", "Vacant", "Occupancy %"],
        "rows": rows,
        "totals": ["Total", t_rooms, t_beds, t_used, max(t_beds - t_used, 0), _pct(t_used, t_beds)],
        "note": f"Allocations active between {date_from:%d %b %Y} and {date_to:%d %b %Y}.",
    }


def vacancy_report(date_from, date_to):
    """Rooms that currently have at least one free bed."""
    Room = _model(ROOM_MODEL, "HMS-F-014")
    rooms = (Room.objects.filter(is_active=True, occupancy__lt=F("capacity"))
             .select_related("block").order_by("block__name", "number"))
    rows = [[r.block.name, r.number, r.capacity, r.occupancy, r.capacity - r.occupancy] for r in rooms]
    return {
        "title": REPORT_TYPES["vacancy"],
        "columns": ["Block", "Room", "Capacity", "Occupied", "Free beds"],
        "rows": rows,
        "totals": ["Total", f"{len(rows)} rooms", "", "", sum(r[4] for r in rows)],
        "note": f"Current availability as of {datetime.date.today():%d %b %Y}.",
    }


def fee_collection_report(date_from, date_to):
    """Successful payments in the range, per term."""
    Payment = _model(PAYMENT_MODEL, "HMS-F-021")
    in_range = {f"{PAYMENT_DATE_FIELD}__date__gte": date_from, f"{PAYMENT_DATE_FIELD}__date__lte": date_to}
    data = (Payment.objects.filter(status__iexact=PAYMENT_SUCCESS, **in_range)
            .values("statement__term").annotate(n=Count("id"), amount=Sum("amount")).order_by("statement__term"))
    rows = [[d["statement__term"], d["n"], d["amount"] or 0] for d in data]
    return {
        "title": REPORT_TYPES["fee-collection"],
        "columns": ["Term", "Payments", "Amount collected"],
        "rows": rows,
        "totals": ["Total", sum(r[1] for r in rows), sum(r[2] for r in rows)],
        "note": f"Successful payments from {date_from:%d %b %Y} to {date_to:%d %b %Y}.",
    }


def defaulters_report(date_from, date_to):
    """Students whose dues fell due inside the range and are still unpaid as of today."""
    Statement = _model(STATEMENT_MODEL, "HMS-F-020")
    qs = (Statement.objects.filter(due_date__gte=date_from, due_date__lte=date_to,
                                   due_date__lt=datetime.date.today(), amount_paid__lt=F("amount_due"))
          .select_related("student").order_by("due_date", "student__username"))
    rows = [[s.student.get_full_name() or s.student.username, s.student.roll_number or "-", s.term,
             s.amount_due, s.amount_paid, s.amount_due - s.amount_paid, s.due_date] for s in qs]
    return {
        "title": REPORT_TYPES["defaulters"],
        "columns": ["Student", "Roll number", "Term", "Due", "Paid", "Balance", "Due date"],
        "rows": rows,
        "totals": ["Total", f"{len(rows)} students", "", "", "", sum(r[5] for r in rows), ""],
        "note": f"Unpaid dues with due dates from {date_from:%d %b %Y} to {date_to:%d %b %Y}.",
    }


def _pct(part, whole):
    return round(100 * part / whole, 1) if whole else 0.0
