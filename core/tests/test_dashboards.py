from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.urls import reverse

from accounts.models import User
from fees.models import FeeStatement
from fees.services import CURRENT_TERM


@pytest.fixture
def student():
    return User.objects.create_user(
        "dashboard_student",
        email="dashboard-student@pes.edu",
        password="test-password",
        role=User.Role.STUDENT,
    )


@pytest.fixture
def admin():
    return User.objects.create_user(
        "dashboard_admin",
        email="dashboard-admin@pes.edu",
        password="test-password",
        role=User.Role.ADMIN,
        is_staff=True,
        is_superuser=True,
    )


@pytest.mark.django_db
def test_student_dashboard_shows_room_and_current_balance(
    client, student, monkeypatch
):
    room = SimpleNamespace(
        block=SimpleNamespace(name="Block A"),
        room_number="101",
    )
    allocation = SimpleNamespace(room=room, room_id=1)
    monkeypatch.setattr(
        "core.views.get_active_allocation", lambda _user: allocation
    )
    FeeStatement.objects.create(
        student=student,
        term=CURRENT_TERM,
        amount_due=Decimal("25000.00"),
        amount_paid=Decimal("7500.00"),
        due_date=date(2026, 8, 1),
    )
    client.force_login(student)

    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assert response.context["block_name"] == "Block A"
    assert response.context["room"] == "101"
    content = response.content.decode()
    assert "Block A" in content
    assert "101" in content
    assert "Balance: 17500.00" in content
    assert "Due date: Aug. 1, 2026" in content


@pytest.mark.django_db
def test_admin_dashboard_shows_occupancy_numbers(client, admin, monkeypatch):
    monkeypatch.setattr(
        "core.views._get_room_occupancy",
        lambda: {
            "total_beds": 120,
            "occupied_beds": 90,
            "vacant_beds": 30,
            "occupancy_percent": 75.0,
        },
    )
    client.force_login(admin)

    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Total beds: 120" in content
    assert "Occupied: 90" in content
    assert "Vacant: 30" in content
    assert "Occupancy: 75.0%" in content


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "expected_paths", "unexpected_paths"),
    [
        (
            User.Role.STUDENT,
            ("/fees/my/", "/complaints/"),
            ("/fees/structures/", "/allocation/", "/reports/"),
        ),
        (
            User.Role.WARDEN,
            ("/fees/structures/",),
            ("/fees/my/", "/complaints/", "/allocation/", "/reports/"),
        ),
    ],
)
def test_navigation_is_role_based_and_skips_unregistered_urls(
    client, role, expected_paths, unexpected_paths
):
    user = User.objects.create_user(
        f"dashboard_{role.lower()}",
        email=f"dashboard-{role.lower()}@pes.edu",
        password="test-password",
        role=role,
    )
    client.force_login(user)

    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    for path in expected_paths:
        assert f'href="{path}"' in response.content.decode()
    for path in unexpected_paths:
        assert f'href="{path}"' not in response.content.decode()
@pytest.mark.django_db


def test_technician_cannot_access_admin_dashboard(client):
    technician = User.objects.create_user(
        "dashboard_technician",
        email="dashboard-technician@pes.edu",
        password="test-password",
        role=User.Role.TECHNICIAN,
    )
    client.force_login(technician)

    response = client.get(reverse("core:home"))

    assert response.status_code == 403
