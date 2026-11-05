import datetime

import pytest
from django.urls import reverse

from accounts.models import User
from reports.services import ReportUnavailable, build_report

from .conftest import TODAY

MONTH_AGO = TODAY - datetime.timedelta(days=31)


def test_occupancy_matches_allocations(hostel):
    """TC-Rep-01 / AC-F-040: figures match the underlying allocation records."""
    report = build_report("occupancy", MONTH_AGO, TODAY)
    assert report["rows"] == [["Block A", 2, 4, 2, 2, 50.0], ["Block B", 1, 1, 1, 0, 100.0]]
    assert report["totals"] == ["Total", 3, 5, 3, 2, 60.0]


def test_occupancy_range_includes_old_allocation(hostel):
    """An allocation that ended 300 days ago counts only when the range covers it."""
    old = build_report("occupancy", TODAY - datetime.timedelta(days=365), TODAY - datetime.timedelta(days=330))
    assert old["totals"][3] == 1


def test_vacancy_lists_rooms_with_free_beds(hostel):
    report = build_report("vacancy", MONTH_AGO, TODAY)
    assert report["rows"] == [["Block A", "A102", 2, 0, 2]]
    assert report["totals"][-1] == 2


def test_fee_collection_counts_only_successful_payments(fees):
    report = build_report("fee-collection", MONTH_AGO, TODAY)
    assert report["rows"] == [["2026-ODD", 2, 85000]]


def test_defaulters_are_past_due_with_balance(statements):
    report = build_report("defaulters", MONTH_AGO, TODAY + datetime.timedelta(days=30))
    assert len(report["rows"]) == 1
    name, roll, term, due, paid, balance, due_date = report["rows"][0]
    assert (roll, due, paid, balance) == ("R1", 65000, 20000, 45000)


def test_invalid_date_range_rejected(db):
    with pytest.raises(ValueError):
        build_report("occupancy", TODAY, MONTH_AGO)


def test_unknown_report_type_rejected(db):
    with pytest.raises(ValueError):
        build_report("salaries", MONTH_AGO, TODAY)


def test_report_page_renders_table(admin_client, hostel):
    resp = admin_client.get(reverse("reports:index"),
                            {"type": "occupancy", "date_from": MONTH_AGO.isoformat(), "date_to": TODAY.isoformat()})
    assert resp.status_code == 200
    assert "Block A" in resp.content.decode() and "60.0" in resp.content.decode()


def test_report_page_bad_range_is_400(admin_client):
    resp = admin_client.get(reverse("reports:index"),
                            {"type": "occupancy", "date_from": TODAY.isoformat(), "date_to": MONTH_AGO.isoformat()})
    assert resp.status_code == 400
    assert "start date must be on or before" in resp.content.decode()


def test_report_page_without_params_shows_form(admin_client):
    resp = admin_client.get(reverse("reports:index"))
    assert resp.status_code == 200 and "Generate" in resp.content.decode()


def test_students_cannot_open_reports(client, db):
    student = User.objects.create_user("st", email="st@pes.edu", password="Str0ng!pass")
    client.force_login(student)
    assert client.get(reverse("reports:index")).status_code == 403


def test_missing_module_gives_friendly_message(admin_client, monkeypatch):
    def unavailable(*args):
        raise ReportUnavailable("This report needs fees.Payment (HMS-F-021), which is not available yet.")
    monkeypatch.setattr("reports.views.build_report", unavailable)
    query = {"type": "fee-collection", "date_from": MONTH_AGO.isoformat(), "date_to": TODAY.isoformat()}
    resp = admin_client.get(reverse("reports:index"), query)
    assert resp.status_code == 200 and "not available yet" in resp.content.decode()
