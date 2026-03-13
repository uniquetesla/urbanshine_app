from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import NumberSequenceType
from apps.core.number_sequences import format_sequence, next_sequence_value
from django.db.models import Sum


class OrderStatus(models.TextChoices):
    NEU = "neu", "Neu"
    GEPLANT = "geplant", "Geplant"
    IN_BEARBEITUNG = "in_bearbeitung", "In Bearbeitung"
    ABGESCHLOSSEN = "abgeschlossen", "Abgeschlossen"
    ABGERECHNET = "abgerechnet", "Abgerechnet"
    STORNIERT = "storniert", "Storniert"


class PositionStatus(models.TextChoices):
    NEU = "neu", "Neu"
    GEPLANT = "geplant", "Geplant"
    IN_BEARBEITUNG = "in_bearbeitung", "In Bearbeitung"
    ABGESCHLOSSEN = "abgeschlossen", "Abgeschlossen"
    STORNIERT = "storniert", "Storniert"


def map_order_status_to_position_status(order_status):
    status_map = {
        OrderStatus.NEU: PositionStatus.NEU,
        OrderStatus.GEPLANT: PositionStatus.GEPLANT,
        OrderStatus.IN_BEARBEITUNG: PositionStatus.IN_BEARBEITUNG,
        OrderStatus.ABGESCHLOSSEN: PositionStatus.ABGESCHLOSSEN,
        OrderStatus.ABGERECHNET: PositionStatus.ABGESCHLOSSEN,
        OrderStatus.STORNIERT: PositionStatus.STORNIERT,
    }
    return status_map.get(order_status, PositionStatus.NEU)


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
    auftragsart = models.CharField(max_length=120, blank=True, verbose_name="Auftragsart")
    order_type = models.ForeignKey(
        "company.OrderType",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="auftraege",
        verbose_name="Auftragsart (Stammdaten)",
    )
    leistungen = models.TextField(blank=True, verbose_name="Leistungen")
    preisberechnung = models.TextField(blank=True, verbose_name="Preisberechnung")
    gesamtpreis = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Gesamtpreis (€)")
    gesamtzeit_minuten = models.PositiveIntegerField(default=0, verbose_name="Gesamtzeit (Minuten)")
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
        return f"{self.formatted_auftragsnummer} · {self.kunde}"

    @property
    def formatted_auftragsnummer(self):
        return format_sequence(NumberSequenceType.AUFTRAG, self.auftragsnummer)

    @property
    def gesamtzeit_formatiert(self):
        stunden, minuten = divmod(self.gesamtzeit_minuten, 60)
        return f"{stunden} Std. {minuten} Min." if stunden else f"{minuten} Min."

    def recalculate_totals(self, save=True):
        totals = self.positionen.aggregate(
            total=Sum("einzelpreis"),
            minuten=Sum("geschaetzte_dauer_minuten"),
        )
        self.gesamtpreis = totals["total"] or Decimal("0.00")
        self.gesamtzeit_minuten = totals["minuten"] or 0
        self.leistungen = "\n".join(
            f"- {position.leistung.name}: {position.einzelpreis} €"
            for position in self.positionen.select_related("leistung")
        )
        self.preisberechnung = "\n".join(
            f"{position.leistung.name}: Basis {position.leistung.price} € × Faktor {position.verschmutzungsgrad.multiplier}"
            + (f" + Zuschlag {position.zuschlag.name}" if position.zuschlag else "")
            + f" = {position.einzelpreis} €"
            for position in self.positionen.select_related("leistung", "verschmutzungsgrad", "zuschlag")
        )
        if self.order_type:
            self.auftragsart = self.order_type.name
        if save and self.pk:
            self.save(update_fields=["gesamtpreis", "gesamtzeit_minuten", "leistungen", "preisberechnung", "auftragsart", "updated_at"])

    def sync_position_statuses(self):
        target_status = map_order_status_to_position_status(self.status)
        self.positionen.exclude(status=target_status).update(status=target_status)

    def save(self, *args, **kwargs):
        if not self.auftragsnummer:
            self.auftragsnummer = next_sequence_value(NumberSequenceType.AUFTRAG)
        if self.order_type and not self.auftragsart:
            self.auftragsart = self.order_type.name
        super().save(*args, **kwargs)


class OrderPosition(models.Model):
    auftrag = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="positionen", verbose_name="Auftrag")
    leistung = models.ForeignKey("company.Service", on_delete=models.PROTECT, related_name="auftragspositionen", verbose_name="Leistung")
    verschmutzungsgrad = models.ForeignKey(
        "company.SoilingLevel",
        on_delete=models.PROTECT,
        related_name="auftragspositionen",
        verbose_name="Verschmutzungsgrad",
    )
    zuschlag = models.ForeignKey(
        "company.Surcharge",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="auftragspositionen",
        verbose_name="Zuschlag",
    )
    status = models.CharField(max_length=20, choices=PositionStatus.choices, default=PositionStatus.NEU, verbose_name="Status")
    einzelpreis = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Einzelpreis (€)")
    einheit = models.CharField(max_length=30, default="Einheit", verbose_name="Einheit")
    geschaetzte_dauer_minuten = models.PositiveIntegerField(default=0, verbose_name="Dauer (Minuten)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Auftragsposition"
        verbose_name_plural = "Auftragspositionen"

    def __str__(self):
        return f"{self.auftrag.auftragsnummer} · {self.leistung.name}"

    def calculate_price(self):
        base_price = self.leistung.price
        price = base_price * self.verschmutzungsgrad.multiplier
        if self.zuschlag:
            if self.zuschlag.is_percentage:
                price += (price * self.zuschlag.amount) / Decimal("100")
            else:
                price += self.zuschlag.amount
        return price.quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        self.einzelpreis = self.calculate_price()
        self.geschaetzte_dauer_minuten = self.leistung.estimated_duration_minutes
        self.einheit = self.leistung.unit
        super().save(*args, **kwargs)


class OrderAttachment(models.Model):
    auftrag = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="anhaenge", verbose_name="Auftrag")
    datei = models.FileField(upload_to="orders/attachments/%Y/%m/", verbose_name="Datei")
    original_name = models.CharField(max_length=255, blank=True, verbose_name="Dateiname")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hochgeladene_auftragsanhaenge",
        verbose_name="Hochgeladen von",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Auftragsanhang"
        verbose_name_plural = "Auftragsanhänge"

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.original_name or self.datei.name.rsplit("/", 1)[-1]

    @property
    def is_image(self):
        name = self.display_name.lower()
        return name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"))
