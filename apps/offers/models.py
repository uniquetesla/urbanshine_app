from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.db.models import Sum

from apps.core.models import NumberSequenceType
from apps.core.number_sequences import format_sequence, next_sequence_value


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

    @staticmethod
    def _money(value):
        return Decimal(value or "0.00").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def zwischensumme(self):
        total = self.positionen.aggregate(total=Sum("gesamtpreis"))["total"]
        return self._money(total)

    @property
    def rabatt_betrag(self):
        rabatt = (self.zwischensumme * self.rabatt_prozent) / Decimal("100")
        return self._money(rabatt)

    @property
    def gesamtpreis(self):
        return self._money(self.zwischensumme - self.rabatt_betrag)


class OfferItem(models.Model):
    angebot = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="positionen", verbose_name="Angebot")
    bezeichnung = models.CharField(max_length=200, verbose_name="Bezeichnung")
    leistung = models.ForeignKey(
        "company.Service",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="angebotspositionen",
        verbose_name="Leistung",
    )
    verschmutzungsgrad = models.ForeignKey(
        "company.SoilingLevel",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="angebotspositionen",
        verbose_name="Verschmutzungsgrad",
    )
    zuschlag = models.ForeignKey(
        "company.Surcharge",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="angebotspositionen",
        verbose_name="Zuschlag",
    )
    menge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"), verbose_name="Menge")
    einheit = models.CharField(max_length=30, default="Einheit", verbose_name="Einheit")
    einzelpreis = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Einzelpreis (€)")
    gesamtpreis = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name="Gesamtpreis (€)")

    class Meta:
        ordering = ["id"]
        verbose_name = "Angebotsposition"
        verbose_name_plural = "Angebotspositionen"

    def __str__(self):
        return f"{self.bezeichnung} ({self.menge} × {self.einzelpreis} €)"

    def calculate_price(self):
        if not self.leistung or not self.verschmutzungsgrad:
            return self.einzelpreis or Decimal("0.00")

        price = self.leistung.price * self.verschmutzungsgrad.multiplier
        if self.zuschlag:
            if self.zuschlag.is_percentage:
                price += (price * self.zuschlag.amount) / Decimal("100")
            else:
                price += self.zuschlag.amount
        return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        if self.leistung and self.verschmutzungsgrad:
            self.bezeichnung = self.leistung.name
            self.einheit = self.leistung.unit
            self.einzelpreis = self.calculate_price()
        self.gesamtpreis = (self.menge * self.einzelpreis).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)
