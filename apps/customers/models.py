from django.db import models
from django.db.models import Max


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
        return f"{self.kundennummer} · {self.vorname} {self.nachname}"

    def save(self, *args, **kwargs):
        if not self.kundennummer:
            last_number = Customer.objects.aggregate(last=Max("kundennummer"))["last"] or 0
            self.kundennummer = last_number + 1
        super().save(*args, **kwargs)
