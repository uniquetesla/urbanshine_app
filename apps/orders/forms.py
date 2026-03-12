from django import forms
from django.core.exceptions import ValidationError

from apps.accounts.models import UserRole
from apps.customers.models import Customer

from .models import Order


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class OrderForm(forms.ModelForm):
    kunden_suche = forms.CharField(label="Kunde suchen", required=True)
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
        self.fields["kunde"].widget = forms.HiddenInput()
        self.fields["mitarbeiter"].queryset = self.fields["mitarbeiter"].queryset.filter(
            role__in=[UserRole.ADMIN, UserRole.CHEF, UserRole.MITARBEITER]
        )
        self.customer_suggestions = [
            f"{customer.kundennummer} · {customer.vorname} {customer.nachname}"
            for customer in Customer.objects.order_by("nachname", "vorname")
        ]
        if self.instance and self.instance.pk:
            self.fields["kunden_suche"].initial = (
                f"{self.instance.kunde.kundennummer} · "
                f"{self.instance.kunde.vorname} {self.instance.kunde.nachname}"
            )

    def clean_kunden_suche(self):
        value = (self.cleaned_data.get("kunden_suche") or "").strip()
        if not value:
            raise ValidationError("Bitte einen Kunden auswählen.")

        kundennummer_raw = value.split("·", 1)[0].strip()
        if kundennummer_raw.isdigit():
            customer = Customer.objects.filter(kundennummer=int(kundennummer_raw)).first()
            if customer:
                self.cleaned_data["kunde"] = customer
                return value

        customer = Customer.objects.filter(
            vorname__iexact=value.split(" ", 1)[0],
            nachname__iexact=value.split(" ", 1)[1] if " " in value else value,
        ).first()
        if not customer:
            raise ValidationError("Kunde wurde nicht gefunden. Bitte aus der Vorschlagsliste auswählen.")
        self.cleaned_data["kunde"] = customer
        return value

    def clean_bilder(self):
        return self.files.getlist("bilder")
