from django.db import models


class NamedBaseModel(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="Name")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class Service(NamedBaseModel):
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Preis (€)")
    estimated_duration_minutes = models.PositiveIntegerField(default=60, verbose_name="Geschätzte Dauer (Minuten)")
    description = models.TextField(blank=True, verbose_name="Beschreibung")

    class Meta(NamedBaseModel.Meta):
        verbose_name = "Leistung"
        verbose_name_plural = "Leistungen"


class Price(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="Bezeichnung")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preis")
    unit = models.CharField(max_length=50, blank=True, verbose_name="Einheit")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")

    class Meta:
        ordering = ["name"]
        verbose_name = "Preis"
        verbose_name_plural = "Preise"

    def __str__(self):
        return f"{self.name} ({self.amount} €)"


class OrderType(NamedBaseModel):
    class Meta(NamedBaseModel.Meta):
        verbose_name = "Auftragsart"
        verbose_name_plural = "Auftragsarten"


class SoilingLevel(NamedBaseModel):
    multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, verbose_name="Faktor")

    class Meta(NamedBaseModel.Meta):
        verbose_name = "Verschmutzungsgrad"
        verbose_name_plural = "Verschmutzungsgrade"


class Surcharge(NamedBaseModel):
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Wert")
    is_percentage = models.BooleanField(default=False, verbose_name="Prozentual")

    class Meta(NamedBaseModel.Meta):
        verbose_name = "Zuschlag"
        verbose_name_plural = "Zuschläge"


class CompanySettings(models.Model):
    company_name = models.CharField(max_length=180, verbose_name="Firmenname")
    address = models.TextField(blank=True, verbose_name="Adresse")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="E-Mail")
    logo = models.ImageField(upload_to="company/", blank=True, null=True, verbose_name="Logo")
    invoice_generation_enabled = models.BooleanField(default=True, verbose_name="Rechnungserstellung aktiv")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Firmendaten"
        verbose_name_plural = "Firmendaten"

    def __str__(self):
        return self.company_name
