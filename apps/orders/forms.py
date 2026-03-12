from django import forms

from apps.accounts.models import UserRole

from .models import Order


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class OrderForm(forms.ModelForm):
    bilder = forms.FileField(
        required=False,
        widget=MultiFileInput(),
        label="Bilder Upload",
    )

    class Meta:
        model = Order
        fields = [
            "kunde",
            "auftragsart",
            "leistungen",
            "verschmutzungsgrad",
            "zuschlaege",
            "preisberechnung",
            "gesamtpreis",
            "status",
            "termin",
            "mitarbeiter",
            "interne_notizen",
        ]
        widgets = {
            "leistungen": forms.Textarea(attrs={"rows": 4}),
            "preisberechnung": forms.Textarea(attrs={"rows": 4}),
            "interne_notizen": forms.Textarea(attrs={"rows": 4}),
            "termin": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "mitarbeiter": forms.SelectMultiple(attrs={"size": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["mitarbeiter"].queryset = self.fields["mitarbeiter"].queryset.filter(
            role__in=[UserRole.ADMIN, UserRole.CHEF, UserRole.MITARBEITER]
        )

    def clean_bilder(self):
        return self.files.getlist("bilder")
