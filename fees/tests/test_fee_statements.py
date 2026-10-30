from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.urls import reverse

from accounts.models import User
from fees.models import FeeStatement, FeeStructure
from fees.services import CURRENT_TERM, NoFeeStructure, get_or_create_statement


@pytest.fixture
def student(db):
    return User.objects.create_user(
        "fee_statement_student",
        email="fee-statement-student@pes.edu",
        password="test-password",
        role=User.Role.STUDENT,
    )


@pytest.fixture
def active_allocation(monkeypatch):
    def set_room_type(room_type):
        def get_allocation(student):
            return SimpleNamespace(
                student=student,
                room=SimpleNamespace(room_type=room_type),
            )

        monkeypatch.setattr(
            "fees.services.get_active_allocation",
            get_allocation,
        )

    return set_room_type


def create_structure(room_type, amount):
    return FeeStructure.objects.create(
        term=CURRENT_TERM,
        room_type=room_type,
        amount=Decimal(amount),
        due_date=date(2026, 8, 1),
        effective_from=date(2026, 7, 1),
    )


def test_statement_uses_fee_structure_for_allocated_room_type(
    student, active_allocation
):
    create_structure(FeeStructure.RoomType.SINGLE, "25000.00")
    shared_structure = create_structure(FeeStructure.RoomType.SHARED, "18000.00")
    active_allocation(FeeStructure.RoomType.SHARED)

    statement = get_or_create_statement(student, CURRENT_TERM)

    assert statement.amount_due == shared_structure.amount
    assert statement.due_date == shared_structure.due_date


def test_existing_statement_amount_stays_fixed_after_structure_edit(
    student, active_allocation
):
    structure = create_structure(FeeStructure.RoomType.SINGLE, "25000.00")
    active_allocation(FeeStructure.RoomType.SINGLE)
    statement = get_or_create_statement(student, CURRENT_TERM)

    structure.amount = Decimal("30000.00")
    structure.save(update_fields=["amount"])

    assert get_or_create_statement(student, CURRENT_TERM).pk == statement.pk
    statement.refresh_from_db()
    assert statement.amount_due == Decimal("25000.00")


def test_fee_statement_balance_is_due_minus_paid(client, student):
    statement = FeeStatement.objects.create(
        student=student,
        term=CURRENT_TERM,
        amount_due=Decimal("25000.00"),
        amount_paid=Decimal("7500.00"),
        due_date=date(2026, 8, 1),
    )
    client.force_login(student)

    assert statement.balance == Decimal("17500.00")
    response = client.get(reverse("fees:my_fees"))
    assert response.status_code == 200
    assert b"17500.00" in response.content


def test_missing_fee_structure_raises_no_fee_structure(student, active_allocation):
    active_allocation(FeeStructure.RoomType.SINGLE)

    with pytest.raises(NoFeeStructure):
        get_or_create_statement(student, CURRENT_TERM)


def test_student_sees_only_their_own_fee_statement(client, student):
    other_student = User.objects.create_user(
        "other_fee_student",
        email="other-fee-student@pes.edu",
        password="test-password",
        role=User.Role.STUDENT,
    )
    FeeStatement.objects.create(
        student=student,
        term="2026-ODD",
        amount_due=Decimal("25000.00"),
        due_date=date(2026, 8, 1),
    )
    FeeStatement.objects.create(
        student=other_student,
        term="2026-EVEN",
        amount_due=Decimal("99000.00"),
        due_date=date(2027, 1, 1),
    )
    client.force_login(student)

    response = client.get(reverse("fees:my_fees"))

    assert response.status_code == 200
    assert "2026-ODD" in response.content.decode()
    assert "2026-EVEN" not in response.content.decode()
    assert "99000.00" not in response.content.decode()


def test_student_without_allocation_sees_no_statement_message(client, student):
    client.force_login(student)

    response = client.get(reverse("fees:my_fees"))

    assert response.status_code == 200
    assert (
        b"No fee statement yet. You have not been allocated a room."
        in response.content
    )
