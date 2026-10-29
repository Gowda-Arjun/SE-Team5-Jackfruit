from django.db import models
from django.db.models import Q


class FeeStructure(models.Model):
    class RoomType(models.TextChoices):
        SINGLE = "SINGLE", "Single"
        SHARED = "SHARED", "Shared"

    term = models.CharField(max_length=20)
    room_type = models.CharField(max_length=10, choices=RoomType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    effective_from = models.DateField()

    class Meta:
        ordering = ["-effective_from", "term", "room_type"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="fees_structure_amount_positive",
            ),
            models.UniqueConstraint(
                fields=["term", "room_type"],
                name="fees_structure_term_room_type_unique",
            ),
        ]

    def __str__(self):
        return f"{self.term} {self.get_room_type_display()} fee"
