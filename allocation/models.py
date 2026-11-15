import datetime

from django.db import models


class Block(models.Model):
    """Hostel block, e.g. Block A or Block B with gender policy (HMS-F-014)."""

    class GenderPolicy(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    name = models.CharField(max_length=64, unique=True)
    gender_policy = models.CharField(max_length=1, choices=GenderPolicy.choices)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_gender_policy_display()})"


class Room(models.Model):
    """Room within a hostel block with floor, capacity, and occupancy (HMS-F-014)."""

    class RoomType(models.TextChoices):
        SINGLE = "SINGLE", "Single"
        SHARED = "SHARED", "Shared"

    block = models.ForeignKey(Block, on_delete=models.PROTECT, related_name="rooms")
    floor = models.IntegerField()
    number = models.CharField(max_length=16)
    room_type = models.CharField(max_length=8, choices=RoomType.choices)
    capacity = models.PositiveIntegerField()
    occupancy = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["block__name", "floor", "number"]
        constraints = [
            models.UniqueConstraint(fields=["block", "number"], name="unique_block_room_number"),
            models.CheckConstraint(
                condition=models.Q(occupancy__gte=0) & models.Q(occupancy__lte=models.F("capacity")),
                name="check_occupancy_within_capacity",
            ),
        ]

    def __str__(self):
        return f"{self.block.name} - Room {self.number}"


class Allocation(models.Model):
    """Room allocation record for a student (HMS-F-012, HMS-F-015)."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ENDED = "ENDED", "Ended"

    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    start_date = models.DateField(default=datetime.date.today)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["-start_date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["student"],
                condition=models.Q(status="ACTIVE"),
                name="unique_active_student_allocation",
            )
        ]

    def __str__(self):
        return f"{self.student.username} -> {self.room} ({self.status})"


class RoomChangeRequest(models.Model):
    """Student request for changing room allocation (HMS-F-013, TC-Alloc-04)."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="room_change_requests",
    )
    current_room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name="change_requests_current",
    )
    preferred_room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="change_requests_preferred",
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    decided_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decided_room_changes",
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student"],
                condition=models.Q(status="PENDING"),
                name="unique_pending_room_change_request",
            )
        ]

    def __str__(self):
        return f"ChangeRequest #{self.pk} - {self.student.username} ({self.status})"
