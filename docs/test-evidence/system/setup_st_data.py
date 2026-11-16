"""Pre-conditions for the system test run, applied after `seed_demo` (STP 6.3).

Run with: python manage.py shell < docs/test-evidence/system/setup_st_data.py

* student01 and student04 share room A103 (roommates for ST_06).
* student03 is in A102 with a statement already past its due date (a defaulter for ST_12).
* tech01 is a Technician account (RBAC check in ST_18).
"""
import datetime

from accounts.models import User
from allocation.models import Room
from allocation.services import allocate_room
from fees.models import FeeStructure
from fees.services import get_or_create_statement

PASSWORD = "Hostel@Demo2026"
TERM = "2026-ODD"

admin = User.objects.get(username="admin")
allocate_room(User.objects.get(username="student01"), Room.objects.get(number="A103"), admin)
allocate_room(User.objects.get(username="student04"), Room.objects.get(number="A103"), admin)

student03 = User.objects.get(username="student03")
allocate_room(student03, Room.objects.get(number="A102"), admin)
structure = FeeStructure.objects.get(term=TERM, room_type="SHARED")
original_due = structure.due_date
structure.due_date = datetime.date.today() - datetime.timedelta(days=5)
structure.save()
get_or_create_statement(student03, TERM)
structure.due_date = original_due
structure.save()

tech, created = User.objects.get_or_create(
    username="tech01",
    defaults={"email": "tech01@demo.hms.test", "role": User.Role.TECHNICIAN, "first_name": "Demo Technician"},
)
if created:
    tech.set_password(PASSWORD)
    tech.save()

print("system test pre-conditions ready")
