"""Shared fixtures for report tests.

Reports read Allocation (Arjun) and Fee (Armaan) models. Tests that need a model that has not
been merged yet are skipped automatically, so CI stays green before those PRs land and the
full checks run as soon as they do.
"""
import datetime

import pytest
from django.apps import apps

from accounts.models import User

TODAY = datetime.date.today()


def model_or_skip(app_label, name):
    try:
        return apps.get_model(app_label, name)
    except LookupError:
        pytest.skip(f"{app_label}.{name} not merged yet")


@pytest.fixture
def admin_client(client, db):
    admin = User.objects.create_user("rep_admin", email="ra@pes.edu", password="Str0ng!pass", role=User.Role.ADMIN)
    client.force_login(admin)
    return client


@pytest.fixture
def students(db):
    return [User.objects.create_user(f"s{i}", email=f"s{i}@pes.edu", password="Str0ng!pass",
                                     roll_number=f"R{i}", first_name=f"Stu{i}") for i in range(4)]


@pytest.fixture
def hostel(db, students):
    """Block A: 2 rooms x 2 beds; Block B: 1 room x 1 bed. Three allocations, one ended last year."""
    Block = model_or_skip("allocation", "Block")
    Room = model_or_skip("allocation", "Room")
    Allocation = model_or_skip("allocation", "Allocation")
    a = Block.objects.create(name="Block A", gender_policy="M")
    b = Block.objects.create(name="Block B", gender_policy="F")
    a1 = Room.objects.create(block=a, floor=1, number="A101", room_type="SHARED", capacity=2, occupancy=2)
    a2 = Room.objects.create(block=a, floor=1, number="A102", room_type="SHARED", capacity=2, occupancy=0)
    b1 = Room.objects.create(block=b, floor=1, number="B101", room_type="SINGLE", capacity=1, occupancy=1)
    Allocation.objects.create(student=students[0], room=a1, start_date=TODAY - datetime.timedelta(days=30))
    Allocation.objects.create(student=students[1], room=a1, start_date=TODAY - datetime.timedelta(days=30))
    Allocation.objects.create(student=students[2], room=b1, start_date=TODAY - datetime.timedelta(days=30))
    Allocation.objects.create(student=students[3], room=a2, start_date=TODAY - datetime.timedelta(days=400),
                              end_date=TODAY - datetime.timedelta(days=300), status="ENDED")
    return {"A101": a1, "A102": a2, "B101": b1}


@pytest.fixture
def statements(db, students):
    """Two statements past due (one fully paid, one partly paid) and one not yet due."""
    Statement = model_or_skip("fees", "FeeStatement")
    past = TODAY - datetime.timedelta(days=5)
    paid = Statement.objects.create(student=students[0], term="2026-ODD", amount_due=65000, amount_paid=65000,
                                    due_date=past)
    partial = Statement.objects.create(student=students[1], term="2026-ODD", amount_due=65000, amount_paid=20000,
                                       due_date=past)
    Statement.objects.create(student=students[2], term="2026-ODD", amount_due=90000, amount_paid=0,
                             due_date=TODAY + datetime.timedelta(days=10))
    return {"paid": paid, "partial": partial}


@pytest.fixture
def fees(statements):
    """Payments against the statements above: two successful, one failed (needs HMS-F-021)."""
    Payment = model_or_skip("fees", "Payment")
    Payment.objects.create(statement=statements["paid"], amount=65000, status="SUCCESS")
    Payment.objects.create(statement=statements["partial"], amount=20000, status="SUCCESS")
    Payment.objects.create(statement=statements["partial"], amount=45000, status="FAILED")
    return statements
