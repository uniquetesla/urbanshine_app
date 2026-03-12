from django.db import models
from django.db.models import Max
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
        verbose_name = "Rechnung"
        verbose_name_plural = "Rechnungen"

    def __str__(self):
        return f"R-{self.rechnungsnummer:05d} · {self.kunde}"

    def save(self, *args, **kwargs):
        if not self.rechnungsnummer:
            last_number = Invoice.objects.aggregate(last=Max("rechnungsnummer"))["last"] or 0
            self.rechnungsnummer = last_number + 1
        super().save(*args, **kwargs)
