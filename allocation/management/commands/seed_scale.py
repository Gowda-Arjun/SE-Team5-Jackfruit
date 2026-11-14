"""Create the deterministic dataset used by HMS-NF-006 scale testing."""

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import StudentProfile, User

from allocation.models import Block, Room


STUDENT_COUNT = 5_000
BLOCK_COUNT = 20
ROOMS_PER_BLOCK = 100
USERNAME_PREFIX = "scale_student"
ROLL_PREFIX = "SCALE2026"
BLOCK_PREFIX = "Scale Block "


class Command(BaseCommand):
    help = "Create the 5,000-student and 2,000-room scale-test dataset."

    @transaction.atomic
    def handle(self, *args, **options):
        blocks = self._seed_blocks()
        users_created, profiles_created = self._seed_students()
        rooms_created = self._seed_rooms(blocks)
        self.stdout.write(
            self.style.SUCCESS(
                "Scale dataset ready: "
                f"{users_created} users, {profiles_created} profiles, {rooms_created} rooms created."
            )
        )

    def _seed_blocks(self):
        blocks = []
        for index in range(1, BLOCK_COUNT + 1):
            block, _ = Block.objects.get_or_create(
                name=f"{BLOCK_PREFIX}{index:02d}",
                defaults={
                    "gender_policy": (
                        Block.GenderPolicy.MALE
                        if index % 2
                        else Block.GenderPolicy.FEMALE
                    )
                },
            )
            blocks.append(block)
        return blocks

    def _seed_students(self):
        usernames = [
            f"{USERNAME_PREFIX}{index:05d}"
            for index in range(1, STUDENT_COUNT + 1)
        ]
        existing_users = User.objects.in_bulk(usernames, field_name="username")
        missing_users = [
            User(
                username=username,
                email=f"{username}@scale.hms.test",
                roll_number=f"{ROLL_PREFIX}{index:05d}",
                role=User.Role.STUDENT,
                first_name=f"Scale Student {index:05d}",
                is_active=True,
            )
            for index, username in enumerate(usernames, start=1)
            if username not in existing_users
        ]
        for user in missing_users:
            user.set_unusable_password()
        User.objects.bulk_create(missing_users, batch_size=500)

        users = User.objects.in_bulk(usernames, field_name="username")
        existing_profile_ids = set(
            StudentProfile.objects.filter(user_id__in=[user.pk for user in users.values()])
            .values_list("user_id", flat=True)
        )
        missing_profiles = [
            StudentProfile(
                user=user,
                full_name=f"Scale Student {index:05d}",
                gender=(
                    StudentProfile.Gender.MALE
                    if index % 2
                    else StudentProfile.Gender.FEMALE
                ),
                phone=f"900{index:07d}",
                address="Synthetic scale-test record",
            )
            for index, username in enumerate(usernames, start=1)
            for user in [users[username]]
            if user.pk not in existing_profile_ids
        ]
        StudentProfile.objects.bulk_create(missing_profiles, batch_size=500)
        return len(missing_users), len(missing_profiles)

    def _seed_rooms(self, blocks):
        block_ids = [block.pk for block in blocks]
        existing_rooms = set(
            Room.objects.filter(block_id__in=block_ids).values_list("block_id", "number")
        )
        missing_rooms = [
            Room(
                block=block,
                floor=(room_index - 1) // 20 + 1,
                number=f"S{block_index:02d}-{room_index:03d}",
                room_type=Room.RoomType.SHARED,
                capacity=4,
                occupancy=0,
                is_active=True,
            )
            for block_index, block in enumerate(blocks, start=1)
            for room_index in range(1, ROOMS_PER_BLOCK + 1)
            if (block.pk, f"S{block_index:02d}-{room_index:03d}") not in existing_rooms
        ]
        Room.objects.bulk_create(missing_rooms, batch_size=500)
        return len(missing_rooms)
