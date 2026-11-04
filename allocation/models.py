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
    is_active = models.BooleanField(default=True)

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
