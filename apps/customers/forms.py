from django import forms

from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "vorname",
            "nachname",
            "strasse",
            "hausnummer",
            "plz",
            "ort",
            "telefon",
            "email",
            "notizen",
        ]
        widgets = {
            "notizen": forms.Textarea(attrs={"rows": 4}),
        }
