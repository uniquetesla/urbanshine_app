from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Max


class PaymentMethod(models.TextChoices):
    KARTE = "karte", "Karte"
    UEBERWEISUNG = "ueberweisung", "Überweisung"
    RECHNUNG = "rechnung", "Rechnung"


class Sale(models.Model):
    verkaufsnummer = models.PositiveIntegerField(unique=True, editable=False, db_index=True)
    mitarbeiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="verkaeufe",
        verbose_name="Mitarbeiter",
    )
    kunde = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="verkaeufe",
        verbose_name="Kunde",
        blank=True,
        null=True,
    )
    zahlungsart = models.CharField(max_length=20, choices=PaymentMethod.choices, verbose_name="Zahlungsart")
    gesamtbetrag = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Verkauf"
        verbose_name_plural = "Verkäufe"

    def save(self, *args, **kwargs):
        if not self.verkaufsnummer:
            last_number = Sale.objects.aggregate(last=Max("verkaufsnummer"))["last"] or 0
            self.verkaufsnummer = last_number + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Verkauf #{self.verkaufsnummer}"


class SaleItem(models.Model):
    verkauf = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="positionen", verbose_name="Verkauf")
    artikel = models.ForeignKey("catalog.Article", on_delete=models.PROTECT, related_name="verkaufspositionen")
    menge = models.PositiveIntegerField(default=1)
    einzelpreis = models.DecimalField(max_digits=10, decimal_places=2)
    gesamtpreis = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Verkaufsposition"
        verbose_name_plural = "Verkaufspositionen"

    def __str__(self):
        return f"{self.artikel} x {self.menge}"
