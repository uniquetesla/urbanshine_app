from django.db import models


from apps.core.models import NumberSequenceType
from apps.core.number_sequences import format_sequence, next_sequence_value


class Customer(models.Model):
    kundennummer = models.PositiveIntegerField(
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Kundennummer",
    )
    vorname = models.CharField(max_length=120, verbose_name="Vorname")
    nachname = models.CharField(max_length=120, verbose_name="Nachname")
    strasse = models.CharField(max_length=255, verbose_name="Straße")
    hausnummer = models.CharField(max_length=20, verbose_name="Hausnummer")
    plz = models.CharField(max_length=10, verbose_name="PLZ")
    ort = models.CharField(max_length=120, verbose_name="Ort")
    telefon = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="E-Mail")
    notizen = models.TextField(blank=True, verbose_name="Notizen")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nachname", "vorname"]
        verbose_name = "Kunde"
        verbose_name_plural = "Kunden"

    def __str__(self):
        return f"{self.formatted_kundennummer} · {self.vorname} {self.nachname}"

    @property
    def formatted_kundennummer(self):
        return format_sequence(NumberSequenceType.KUNDE, self.kundennummer)

    def save(self, *args, **kwargs):
        if not self.kundennummer:
            self.kundennummer = next_sequence_value(NumberSequenceType.KUNDE)
        super().save(*args, **kwargs)
