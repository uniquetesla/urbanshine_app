from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Max


class OrderStatus(models.TextChoices):
    NEU = "neu", "Neu"
    GEPLANT = "geplant", "Geplant"
    IN_BEARBEITUNG = "in_bearbeitung", "In Bearbeitung"
    ABGESCHLOSSEN = "abgeschlossen", "Abgeschlossen"
    ABGERECHNET = "abgerechnet", "Abgerechnet"
    STORNIERT = "storniert", "Storniert"


class Verschmutzungsgrad(models.TextChoices):
    LEICHT = "leicht", "Leicht"
    NORMAL = "normal", "Normal"
    STARK = "stark", "Stark"
    EXTREM = "extrem", "Extrem"


class Order(models.Model):
    auftragsnummer = models.PositiveIntegerField(
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Auftragsnummer",
    )
    kunde = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="auftraege",
        verbose_name="Kunde",
    )
    auftragsart = models.CharField(max_length=120, verbose_name="Auftragsart")
    leistungen = models.TextField(verbose_name="Leistungen")
    verschmutzungsgrad = models.CharField(
        max_length=20,
        choices=Verschmutzungsgrad.choices,
        default=Verschmutzungsgrad.NORMAL,
        verbose_name="Verschmutzungsgrad",
    )
    zuschlaege = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Zuschläge (€)",
    )
    preisberechnung = models.TextField(verbose_name="Preisberechnung")
    gesamtpreis = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Gesamtpreis (€)")
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.NEU,
        verbose_name="Status",
    )
    termin = models.DateTimeField(null=True, blank=True, verbose_name="Termin")
    mitarbeiter = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="auftraege",
        verbose_name="Mitarbeiter",
    )
    interne_notizen = models.TextField(blank=True, verbose_name="Interne Notizen")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Auftrag"
        verbose_name_plural = "Aufträge"

    def __str__(self):
        return f"{self.auftragsnummer} · {self.kunde}"

    def save(self, *args, **kwargs):
        if not self.auftragsnummer:
            last_number = Order.objects.aggregate(last=Max("auftragsnummer"))["last"] or 0
            self.auftragsnummer = last_number + 1
        super().save(*args, **kwargs)


class OrderImage(models.Model):
    auftrag = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="bilder", verbose_name="Auftrag")
    bild = models.ImageField(upload_to="orders/", verbose_name="Bild")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Auftragsbild"
        verbose_name_plural = "Auftragsbilder"

    def __str__(self):
        return f"Bild zu Auftrag {self.auftrag.auftragsnummer}"
