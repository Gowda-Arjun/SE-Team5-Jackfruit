from django.conf import settings
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


class FeeStatement(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="fee_statements",
    )
    term = models.CharField(max_length=20)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField()

    class Meta:
        ordering = ["term"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "term"],
                name="fees_statement_student_term_unique",
            ),
            models.CheckConstraint(
                condition=Q(amount_paid__gte=0),
                name="fees_statement_amount_paid_nonnegative",
            ),
        ]

    @property
    def balance(self):
        return self.amount_due - self.amount_paid

    def __str__(self):
        return f"{self.student} {self.term} fee statement"
