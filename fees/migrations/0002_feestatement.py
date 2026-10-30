import django.conf
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fees", "0001_initial"),
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FeeStatement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("term", models.CharField(max_length=20)),
                ("amount_due", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "amount_paid",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=10,
                    ),
                ),
                ("due_date", models.DateField()),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="fee_statements",
                        to=django.conf.settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["term"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("student", "term"),
                        name="fees_statement_student_term_unique",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("amount_paid__gte", 0)),
                        name="fees_statement_amount_paid_nonnegative",
                    ),
                ],
            },
        ),
    ]
