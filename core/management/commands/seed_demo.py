"""Seed synthetic demo/test data (STP 6.3; backlog HMS-03).

    python manage.py seed_demo

Creates (idempotently - safe to run again):
  * admin   / warden            - Admin and Warden accounts (admin can also open /admin/)
  * student01 ... student10     - students with profiles (01-05 male, 06-10 female)
  * Blocks A (male) and B (female) with 5 rooms each    - once allocation.Block/Room exist (HMS-09)
  * One fee structure per room type for term 2026-ODD  - once fees.FeeStructure exists (HMS-14)

All accounts use the password in DEMO_PASSWORD below. Synthetic data only - never real students.
"""
import datetime

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import StudentProfile, User

DEMO_PASSWORD = "Hostel@Demo2026"
TERM = "2026-ODD"


class Command(BaseCommand):
    help = "Create synthetic demo users, hostel blocks/rooms and fee structures."

    @transaction.atomic
    def handle(self, *args, **options):
        self.seed_users()
        self.seed_rooms()
        self.seed_fees()
        self.stdout.write(self.style.SUCCESS(f"Demo data ready. Password for all demo accounts: {DEMO_PASSWORD}"))

    def make_user(self, username, role, **extra):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": f"{username}@demo.hms.test", "role": role, **extra},
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user

    def seed_users(self):
        self.make_user("admin", User.Role.ADMIN, is_staff=True, is_superuser=True, first_name="Demo Admin")
        self.make_user("warden", User.Role.WARDEN, first_name="Demo Warden")
        for i in range(1, 11):
            gender = StudentProfile.Gender.MALE if i <= 5 else StudentProfile.Gender.FEMALE
            user = self.make_user(f"student{i:02d}", User.Role.STUDENT, roll_number=f"DEMO2026{i:03d}",
                                  first_name=f"Student {i:02d}")
            StudentProfile.objects.get_or_create(
                user=user,
                defaults={"full_name": f"Demo Student {i:02d}", "gender": gender, "phone": f"90000000{i:02d}",
                          "guardian_name": f"Guardian {i:02d}", "emergency_contact": f"Guardian {i:02d}"},
            )
        self.stdout.write("  users: admin, warden, student01-student10")

    def seed_rooms(self):
        try:
            Block = apps.get_model("allocation", "Block")
            Room = apps.get_model("allocation", "Room")
        except LookupError:
            self.stdout.write(self.style.WARNING("  rooms: skipped (allocation models not merged yet - HMS-09)"))
            return
        for block_name, policy in (("A", "M"), ("B", "F")):
            block, _ = Block.objects.get_or_create(name=f"Block {block_name}", defaults={"gender_policy": policy})
            for n in range(1, 6):
                single = n == 1
                Room.objects.get_or_create(
                    block=block, number=f"{block_name}10{n}",
                    defaults={"floor": 1, "room_type": "SINGLE" if single else "SHARED",
                              "capacity": 1 if single else 2, "occupancy": 0, "is_active": True},
                )
        self.stdout.write("  rooms: Block A (male) + Block B (female), 5 rooms each (room x101 is single)")

    def seed_fees(self):
        try:
            FeeStructure = apps.get_model("fees", "FeeStructure")
        except LookupError:
            self.stdout.write(self.style.WARNING("  fees: skipped (fee models not merged yet - HMS-14)"))
            return
        today = datetime.date.today()
        for room_type, amount in (("SINGLE", 90000), ("SHARED", 65000)):
            FeeStructure.objects.get_or_create(
                term=TERM, room_type=room_type,
                defaults={"amount": amount, "due_date": today + datetime.timedelta(days=30), "effective_from": today},
            )
        self.stdout.write(f"  fees: {TERM} single 90000, shared 65000")
