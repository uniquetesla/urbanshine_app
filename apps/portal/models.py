from django.db import models


class AppointmentRequestStatus(models.TextChoices):
    OFFEN = "offen", "Offen"
    IN_BEARBEITUNG = "in_bearbeitung", "In Bearbeitung"
    BESTAETIGT = "bestaetigt", "Bestätigt"
    ABGELEHNT = "abgelehnt", "Abgelehnt"


class AppointmentRequest(models.Model):
    kunde = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="terminanfragen",
        verbose_name="Kunde",
    )
    name = models.CharField(max_length=200, verbose_name="Name")
    email = models.EmailField(verbose_name="E-Mail")
    telefon = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    wunschtermin_datum = models.DateField(verbose_name="Wunschtermin (Datum)")
    wunschtermin_uhrzeit = models.TimeField(verbose_name="Wunschtermin (Uhrzeit)")
    nachricht = models.TextField(blank=True, verbose_name="Nachricht")
    status = models.CharField(
        max_length=20,
        choices=AppointmentRequestStatus.choices,
        default=AppointmentRequestStatus.OFFEN,
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Terminanfrage"
        verbose_name_plural = "Terminanfragen"

    def __str__(self):
        return f"{self.name} · {self.wunschtermin_datum} {self.wunschtermin_uhrzeit}"
