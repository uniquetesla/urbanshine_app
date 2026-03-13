from django.conf import settings
from django.db import models


class DocumentCategory(models.TextChoices):
    VERTRAG = "vertrag", "Vertrag"
    BERICHT = "bericht", "Bericht"
    RECHNUNG = "rechnung", "Rechnung"
    VORLAGE = "vorlage", "Vorlage"
    SONSTIGES = "sonstiges", "Sonstiges"


class CompanyDocument(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titel")
    description = models.TextField(blank=True, verbose_name="Beschreibung")
    category = models.CharField(max_length=30, choices=DocumentCategory.choices, default=DocumentCategory.SONSTIGES, verbose_name="Kategorie")
    file = models.FileField(upload_to="company_documents/", verbose_name="Datei")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Hochgeladen am")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="company_documents",
        verbose_name="Hochgeladen von",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Firmendokument"
        verbose_name_plural = "Firmendokumente"

    def __str__(self):
        return self.title
