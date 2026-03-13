import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("customers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppointmentRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="Name")),
                ("email", models.EmailField(max_length=254, verbose_name="E-Mail")),
                ("telefon", models.CharField(blank=True, max_length=50, verbose_name="Telefon")),
                ("wunschtermin_datum", models.DateField(verbose_name="Wunschtermin (Datum)")),
                ("wunschtermin_uhrzeit", models.TimeField(verbose_name="Wunschtermin (Uhrzeit)")),
                ("nachricht", models.TextField(blank=True, verbose_name="Nachricht")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("offen", "Offen"),
                            ("in_bearbeitung", "In Bearbeitung"),
                            ("bestaetigt", "Bestätigt"),
                            ("abgelehnt", "Abgelehnt"),
                        ],
                        default="offen",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "kunde",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="terminanfragen",
                        to="customers.customer",
                        verbose_name="Kunde",
                    ),
                ),
            ],
            options={
                "verbose_name": "Terminanfrage",
                "verbose_name_plural": "Terminanfragen",
                "ordering": ["-created_at"],
            },
        ),
    ]
