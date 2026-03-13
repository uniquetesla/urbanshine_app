from django import forms

from .models import AppointmentRequest


class AppointmentRequestForm(forms.ModelForm):
    class Meta:
        model = AppointmentRequest
        fields = ["name", "email", "telefon", "wunschtermin_datum", "wunschtermin_uhrzeit", "nachricht"]
        widgets = {
            "wunschtermin_datum": forms.DateInput(attrs={"type": "date"}),
            "wunschtermin_uhrzeit": forms.TimeInput(attrs={"type": "time"}),
            "nachricht": forms.Textarea(attrs={"rows": 4}),
        }
