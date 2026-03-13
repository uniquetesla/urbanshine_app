from decimal import Decimal

from django.db import models

from apps.core.models import NumberSequenceType
from apps.core.number_sequences import format_sequence, next_sequence_value
from django.db.models import Sum


class OfferStatus(models.TextChoices):
    ENTWURF = "entwurf", "Entwurf"
    VERSENDET = "versendet", "Versendet"
    ANGENOMMEN = "angenommen", "Angenommen"
    ABGELEHNT = "abgelehnt", "Abgelehnt"
    UMGEWANDELT = "umgewandelt", "In Auftrag umgewandelt"


class Offer(models.Model):
    angebotsnummer = models.PositiveIntegerField(unique=True, editable=False, db_index=True, verbose_name="Angebotsnummer")
    kunde = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="angebote", verbose_name="Kunde")
    titel = models.CharField(max_length=200, verbose_name="Titel")
    beschreibung = models.TextField(blank=True, verbose_name="Beschreibung")
    rabatt_prozent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name="Rabatt (%)")
    status = models.CharField(max_length=20, choices=OfferStatus.choices, default=OfferStatus.ENTWURF, verbose_name="Status")
    umgewandelter_auftrag = models.OneToOneField(
        "orders.Order",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="quelle_angebot",
        verbose_name="Umgewandelter Auftrag",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-angebotsnummer"]
        verbose_name = "Angebot"
        verbose_name_plural = "Angebote"

    def __str__(self):
        return f"{self.formatted_angebotsnummer} · {self.kunde}"

    @property
    def formatted_angebotsnummer(self):
        return format_sequence(NumberSequenceType.ANGEBOT, self.angebotsnummer)

    def save(self, *args, **kwargs):
        if not self.angebotsnummer:
            self.angebotsnummer = next_sequence_value(NumberSequenceType.ANGEBOT)
        super().save(*args, **kwargs)

    @property
    def zwischensumme(self):
        total = self.positionen.aggregate(total=Sum("gesamtpreis"))["total"]
        return total or Decimal("0.00")

    @property
    def rabatt_betrag(self):
        return (self.zwischensumme * self.rabatt_prozent) / Decimal("100")

    @property
    def gesamtpreis(self):
        return self.zwischensumme - self.rabatt_betrag


class OfferItem(models.Model):
    angebot = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="positionen", verbose_name="Angebot")
    bezeichnung = models.CharField(max_length=200, verbose_name="Bezeichnung")
    menge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"), verbose_name="Menge")
    einzelpreis = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Einzelpreis (€)")
    gesamtpreis = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name="Gesamtpreis (€)")

    class Meta:
        ordering = ["id"]
        verbose_name = "Angebotsposition"
        verbose_name_plural = "Angebotspositionen"

    def __str__(self):
        return f"{self.bezeichnung} ({self.menge} × {self.einzelpreis} €)"

    def save(self, *args, **kwargs):
        self.gesamtpreis = self.menge * self.einzelpreis
        super().save(*args, **kwargs)
