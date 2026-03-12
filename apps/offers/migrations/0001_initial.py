from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("customers", "0001_initial"),
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Offer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("angebotsnummer", models.PositiveIntegerField(db_index=True, editable=False, unique=True, verbose_name="Angebotsnummer")),
                ("titel", models.CharField(max_length=200, verbose_name="Titel")),
                ("beschreibung", models.TextField(blank=True, verbose_name="Beschreibung")),
                (
                    "rabatt_prozent",
                    models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=5, verbose_name="Rabatt (%)"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("entwurf", "Entwurf"),
                            ("versendet", "Versendet"),
                            ("angenommen", "Angenommen"),
                            ("abgelehnt", "Abgelehnt"),
                            ("umgewandelt", "In Auftrag umgewandelt"),
                        ],
                        default="entwurf",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "kunde",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="angebote",
                        to="customers.customer",
                        verbose_name="Kunde",
                    ),
                ),
                (
                    "umgewandelter_auftrag",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="quelle_angebot",
                        to="orders.order",
                        verbose_name="Umgewandelter Auftrag",
                    ),
                ),
            ],
            options={
                "verbose_name": "Angebot",
                "verbose_name_plural": "Angebote",
                "ordering": ["-angebotsnummer"],
            },
        ),
        migrations.CreateModel(
            name="OfferItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bezeichnung", models.CharField(max_length=200, verbose_name="Bezeichnung")),
                ("menge", models.DecimalField(decimal_places=2, default=Decimal("1.00"), max_digits=10, verbose_name="Menge")),
                ("einzelpreis", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Einzelpreis (€)")),
                ("gesamtpreis", models.DecimalField(decimal_places=2, editable=False, max_digits=10, verbose_name="Gesamtpreis (€)")),
                (
                    "angebot",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="positionen",
                        to="offers.offer",
                        verbose_name="Angebot",
                    ),
                ),
            ],
            options={
                "verbose_name": "Angebotsposition",
                "verbose_name_plural": "Angebotspositionen",
                "ordering": ["id"],
            },
        ),
    ]
