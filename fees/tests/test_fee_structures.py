from decimal import Decimal

import pytest
from django.urls import reverse

from accounts.models import User
from audit.models import AuditLog
from fees.models import FeeStructure


@pytest.fixture
def warden(db):
    return User.objects.create_user(
        "fee_warden",
        email="fee-warden@pes.edu",
        password="test-password",
        role=User.Role.WARDEN,
    )


@pytest.fixture
def warden_client(client, warden):
    client.force_login(warden)
    return client


@pytest.fixture
def fee_data():
    return {
        "term": "2026-ODD",
        "room_type": FeeStructure.RoomType.SINGLE,
        "amount": "25000.00",
        "due_date": "2026-08-01",
        "effective_from": "2026-07-01",
    }


def test_warden_can_create_fee_structure_and_audit_it(warden_client, warden, fee_data):
    response = warden_client.post(reverse("fees:structure_create"), fee_data)

    assert response.status_code == 302
    structure = FeeStructure.objects.get()
    assert structure.term == "2026-ODD"
    assert structure.amount == Decimal("25000.00")
    audit = AuditLog.objects.get()
    assert audit.actor == warden
    assert audit.action == "FEE_STRUCTURE_SAVED"
    assert audit.target_type == "FeeStructure"
    assert audit.target_id == str(structure.pk)


def test_duplicate_term_and_room_type_is_rejected(warden_client, fee_data):
    response = warden_client.post(reverse("fees:structure_create"), fee_data)
    assert response.status_code == 302

    response = warden_client.post(reverse("fees:structure_create"), fee_data)
    assert response.status_code == 200
    assert FeeStructure.objects.count() == 1
    assert "already exists" in response.content.decode().lower()
    assert AuditLog.objects.count() == 1


@pytest.mark.parametrize("amount", ["0.00", "-1.00"])
def test_non_positive_amount_is_rejected(warden_client, fee_data, amount):
    fee_data["amount"] = amount

    response = warden_client.post(reverse("fees:structure_create"), fee_data)

    assert response.status_code == 200
    assert not FeeStructure.objects.exists()
    assert not AuditLog.objects.exists()


def test_student_is_forbidden_from_fee_structure_pages(client, db):
    student = User.objects.create_user(
        "fee_student",
        email="fee-student@pes.edu",
        password="test-password",
        role=User.Role.STUDENT,
    )
    client.force_login(student)

    assert client.get(reverse("fees:structure_list")).status_code == 403
    assert client.get(reverse("fees:structure_create")).status_code == 403


def test_edit_saves_changes_and_writes_audit(warden_client, fee_data):
    structure = FeeStructure.objects.create(**{
        **fee_data,
        "amount": Decimal(fee_data["amount"]),
    })
    updated_data = {**fee_data, "amount": "30000.00"}

    response = warden_client.post(
        reverse("fees:structure_edit", args=[structure.pk]),
        updated_data,
    )

    assert response.status_code == 302
    structure.refresh_from_db()
    assert structure.amount == Decimal("30000.00")
    audit = AuditLog.objects.get()
    assert audit.action == "FEE_STRUCTURE_SAVED"
    assert audit.target_id == str(structure.pk)


def test_admin_create_and_edit_are_audited(client, db, fee_data):
    admin = User.objects.create_user(
        "fee_admin",
        email="fee-admin@pes.edu",
        password="test-password",
        role=User.Role.ADMIN,
        is_staff=True,
        is_superuser=True,
    )
    client.force_login(admin)

    response = client.post(reverse("admin:fees_feestructure_add"), fee_data)
    assert response.status_code == 302
    structure = FeeStructure.objects.get()
    audit = AuditLog.objects.get()
    assert audit.action == "FEE_STRUCTURE_SAVED"
    assert audit.target_id == str(structure.pk)

    response = client.post(
        reverse("admin:fees_feestructure_change", args=[structure.pk]),
        {**fee_data, "amount": "30000.00", "_save": "Save"},
    )
    assert response.status_code == 302
    assert AuditLog.objects.count() == 2
