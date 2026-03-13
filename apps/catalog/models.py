from django.conf import settings
from django.db import models

from apps.core.models import NumberSequenceType
from apps.core.number_sequences import format_sequence, next_sequence_value


class Article(models.Model):
    ICON_FELGENREINIGER = "felgenreiniger"
    ICON_INNENREINIGER = "innenreiniger"
    ICON_MIKROFASERTUCH = "mikrofasertuch"
    ICON_POLITUR = "politur"
    ICON_VERSIEGELUNG = "versiegelung"

    ICON_CHOICES = [
        (ICON_FELGENREINIGER, "🛞 Felgenreiniger"),
        (ICON_INNENREINIGER, "🧴 Innenreiniger"),
        (ICON_MIKROFASERTUCH, "🧽 Mikrofasertuch"),
        (ICON_POLITUR, "✨ Politur"),
        (ICON_VERSIEGELUNG, "🛡️ Versiegelung"),
    ]

    artikelnummer = models.PositiveIntegerField(unique=True, null=True, blank=True, editable=False, db_index=True, verbose_name="Artikelnummer")
    barcode = models.CharField(max_length=64, unique=True, null=True, blank=True, verbose_name="Barcode")
    name = models.CharField(max_length=120, verbose_name="Name")
    preis = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preis")
    lagerbestand = models.PositiveIntegerField(default=0, verbose_name="Lagerbestand")
    kategorie = models.CharField(max_length=80, verbose_name="Kategorie")
    icon = models.CharField(max_length=30, choices=ICON_CHOICES, verbose_name="Icon")
    beschreibung = models.TextField(blank=True, verbose_name="Beschreibung")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Artikel"
        verbose_name_plural = "Artikel"

    def __str__(self):
        return f"{self.formatted_artikelnummer} · {self.name}"

    @property
    def formatted_artikelnummer(self):
        return format_sequence(NumberSequenceType.ARTIKEL, self.artikelnummer)

    def save(self, *args, **kwargs):
        if not self.artikelnummer:
            self.artikelnummer = next_sequence_value(NumberSequenceType.ARTIKEL)
        super().save(*args, **kwargs)


class GoodsReceipt(models.Model):
    artikel = models.ForeignKey(Article, on_delete=models.PROTECT, related_name="wareneingaenge", verbose_name="Artikel")
    artikelnummer = models.CharField(max_length=64, verbose_name="Artikelnummer")
    barcode = models.CharField(max_length=64, verbose_name="Barcode")
    menge = models.PositiveIntegerField(verbose_name="Menge")
    notiz = models.CharField(max_length=255, blank=True, verbose_name="Notiz")
    gebucht_von = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="wareneingaenge", verbose_name="Gebucht von")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Gebucht am")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Wareneingang"
        verbose_name_plural = "Wareneingänge"

    def __str__(self):
        return f"{self.artikelnummer} · +{self.menge}"
