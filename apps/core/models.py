from django.conf import settings
from django.db import models


class ActivitySubject(models.TextChoices):
    AUFTRAG = "auftrag", "Auftrag"
    KUNDE = "kunde", "Kunde"
    RECHNUNG = "rechnung", "Rechnung"
    ANGEBOT = "angebot", "Angebot"
    DOKUMENT = "dokument", "Dokument"


class ActivityLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name="Ausgeführt von",
    )
    subject_type = models.CharField(max_length=20, choices=ActivitySubject.choices, verbose_name="Bereich")
    subject_label = models.CharField(max_length=255, verbose_name="Objekt")
    action = models.CharField(max_length=255, verbose_name="Aktion")
    details = models.TextField(blank=True, verbose_name="Details")
    from_state = models.CharField(max_length=120, blank=True, verbose_name="Vorher")
    to_state = models.CharField(max_length=120, blank=True, verbose_name="Nachher")
    icon = models.CharField(max_length=20, default="📝", verbose_name="Icon")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Zeitpunkt")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Aktivität"
        verbose_name_plural = "Aktivitäten"

    def __str__(self):
        return f"{self.get_subject_type_display()} · {self.action}"
