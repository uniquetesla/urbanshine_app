from django.db import models


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
        return self.name
