from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse

from accounts.models import User
from fees.gateway import MockGateway, PaymentGatewayUnavailable
from fees.models import FeeStatement, Payment


@pytest.fixture
def warden(db):
    return User.objects.create_user(
        "reconciliation_warden",
        email="reconciliation-warden@pes.edu",
        password="test-password-123",
        role=User.Role.WARDEN,
    )


@pytest.fixture
def student(db):
    return User.objects.create_user(
        "reconciliation_student",
        email="reconciliation-student@pes.edu",
        password="test-password-123",
        role=User.Role.STUDENT,
        roll_number="RECON-001",
    )


@pytest.fixture
def overdue_statement(student):
    return FeeStatement.objects.create(
        student=student,
        term="2026-ODD",
        amount_due=Decimal("1000.00"),
        amount_paid=Decimal("250.00"),
        due_date=date.today() - timedelta(days=10),
    )


@pytest.fixture
def successful_payment(overdue_statement):
    return Payment.objects.create(
        statement=overdue_statement,
        amount=Decimal("100.00"),
        status=Payment.Status.SUCCESS,
        gateway_order_id="reconcile_order",
        gateway_txn_id="reconcile_txn",
    )


class MismatchedLedgerGateway:
    def fetch_ledger(self, date_from, date_to):
        return [
            {
                "order_id": "reconcile_order",
                "amount": 9900,
                "status": "captured",
            }
        ]


class UnavailableLedgerGateway:
    def fetch_ledger(self, date_from, date_to):
        raise PaymentGatewayUnavailable


def reconciliation_url():
    today = date.today()
    return reverse("fees:reconciliation") + (
        f"?date_from={today.isoformat()}&date_to={today.isoformat()}"
    )


def test_reconciliation_detects_ledger_mismatch(
    client, warden, successful_payment
):
    client.force_login(warden)
    with patch("fees.views.get_gateway", return_value=MismatchedLedgerGateway()):
        response = client.get(reconciliation_url())

    assert response.status_code == 200
    assert response.context["report"]["matched_count"] == 0
    mismatch = response.context["report"]["mismatches"][0]
    assert mismatch["payment"] == successful_payment
    assert mismatch["reason"] == "Amount differs"
    assert b"Amount differs" in response.content


def test_mock_gateway_matches_its_successful_database_payments(
    client, warden, successful_payment
):
    client.force_login(warden)
    with patch("fees.views.get_gateway", return_value=MockGateway()):
        response = client.get(reconciliation_url())

    assert response.status_code == 200
    assert response.context["report"]["matched_count"] == 1
    assert response.context["report"]["mismatches"] == []


def test_reconciliation_defaulters_match_overdue_unpaid_statements(
    client, warden, student, overdue_statement
):
    FeeStatement.objects.create(
        student=student,
        term="2026-EVEN",
        amount_due=Decimal("500.00"),
        amount_paid=Decimal("0.00"),
        due_date=date.today() + timedelta(days=10),
    )
    client.force_login(warden)
    with patch("fees.views.get_gateway", return_value=MockGateway()):
        response = client.get(reconciliation_url())

    assert response.status_code == 200
    defaulters = response.context["report"]["defaulters"]
    assert len(defaulters) == 1
    assert defaulters[0] == {
        "student": student.username,
        "roll_number": "RECON-001",
        "term": "2026-ODD",
        "balance": Decimal("750.00"),
        "due_date": overdue_statement.due_date,
    }


def test_student_is_forbidden_from_reconciliation(client, student):
    client.force_login(student)

    response = client.get(reverse("fees:reconciliation"))

    assert response.status_code == 403


def test_gateway_outage_shows_service_unavailable_message(client, warden):
    client.force_login(warden)
    with patch(
        "fees.views.get_gateway",
        return_value=UnavailableLedgerGateway(),
    ):
        response = client.get(reconciliation_url())

    assert response.status_code == 200
    assert b"Payment service is not available right now." in response.content
    assert response.context["report"] is None
