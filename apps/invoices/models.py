from django.db import models

from apps.core.models import NumberSequenceType
from apps.core.number_sequences import format_sequence, next_sequence_value
from django.utils import timezone


class PaymentStatus(models.TextChoices):
    OFFEN = "offen", "Offen"
    TEILWEISE_BEZAHLT = "teilweise_bezahlt", "Teilweise bezahlt"
    BEZAHLT = "bezahlt", "Bezahlt"
    UEBERFAELLIG = "ueberfaellig", "Überfällig"
    STORNIERT = "storniert", "Storniert"


class Invoice(models.Model):
    rechnungsnummer = models.PositiveIntegerField(
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Rechnungsnummer",
    )
    kunde = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="rechnungen",
        verbose_name="Kunde",
    )
    auftrag = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        related_name="rechnungen",
        blank=True,
        null=True,
        verbose_name="Auftrag",
    )
    verkauf = models.OneToOneField(
        "checkout.Sale",
        on_delete=models.SET_NULL,
        related_name="rechnung",
        blank=True,
        null=True,
        verbose_name="Verkauf",
    )
    rechnungsdatum = models.DateField(default=timezone.localdate, verbose_name="Rechnungsdatum")
    faellig_am = models.DateField(blank=True, null=True, verbose_name="Fällig am")
    betrag = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Betrag")
    zahlungsstatus = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.OFFEN,
        verbose_name="Zahlungsstatus",
    )
    notizen = models.TextField(blank=True, verbose_name="Notizen")
    pdf_datei = models.FileField(upload_to="invoices/", blank=True, null=True, verbose_name="PDF-Datei")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-rechnungsdatum", "-rechnungsnummer"]
        constraints = [
            models.UniqueConstraint(fields=["auftrag"], name="unique_invoice_per_order"),
        ]
        verbose_name = "Rechnung"
        verbose_name_plural = "Rechnungen"

    def __str__(self):
        return f"{self.formatted_rechnungsnummer} · {self.kunde}"

    @property
    def formatted_rechnungsnummer(self):
        return format_sequence(NumberSequenceType.RECHNUNG, self.rechnungsnummer)

    def save(self, *args, **kwargs):
        if not self.rechnungsnummer:
            self.rechnungsnummer = next_sequence_value(NumberSequenceType.RECHNUNG)
        super().save(*args, **kwargs)
