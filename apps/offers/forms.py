from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from apps.company.models import Service, SoilingLevel, Surcharge
from apps.core.number_sequences import parse_sequence_value
from apps.customers.models import Customer

from .models import Offer, OfferItem


class OfferForm(forms.ModelForm):
    kunden_suche = forms.CharField(label="Kunde suchen", required=True)

    class Meta:
        model = Offer
        fields = ["kunde", "titel", "beschreibung", "rabatt_prozent", "status"]
        widgets = {
            "beschreibung": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["kunde"].widget = forms.HiddenInput()
        self.fields["kunde"].required = False
        self.customer_suggestions = [
            f"{customer.formatted_kundennummer} · {customer.vorname} {customer.nachname}"
            for customer in Customer.objects.order_by("nachname", "vorname")
        ]
        if self.instance and self.instance.pk:
            self.fields["kunden_suche"].initial = (
                f"{self.instance.kunde.formatted_kundennummer} · {self.instance.kunde.vorname} {self.instance.kunde.nachname}"
            )

    def clean_kunden_suche(self):
        value = (self.cleaned_data.get("kunden_suche") or "").strip()
        if not value:
            raise ValidationError("Bitte einen Kunden auswählen.")

        kundennummer_raw = value.split("·", 1)[0].strip()
        kundennummer = parse_sequence_value(kundennummer_raw)
        if kundennummer is not None:
            customer = Customer.objects.filter(kundennummer=kundennummer).first()
            if customer:
                self.cleaned_data["kunde"] = customer
                return value

        raise ValidationError("Kunde wurde nicht gefunden. Bitte aus der Vorschlagsliste auswählen.")

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("kunde"):
            self.add_error("kunden_suche", "Bitte einen gültigen Kunden aus der Liste auswählen.")
        return cleaned_data


class OfferItemForm(forms.ModelForm):
    class Meta:
        model = OfferItem
        fields = ["leistung", "verschmutzungsgrad", "zuschlag", "menge", "einheit"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        service_qs = Service.objects.filter(is_active=True)
        soiling_qs = SoilingLevel.objects.filter(is_active=True)
        surcharge_qs = Surcharge.objects.filter(is_active=True)

        if self.instance and self.instance.pk:
            if self.instance.leistung_id:
                service_qs = Service.objects.filter(pk=self.instance.leistung_id) | service_qs
            if self.instance.verschmutzungsgrad_id:
                soiling_qs = SoilingLevel.objects.filter(pk=self.instance.verschmutzungsgrad_id) | soiling_qs
            if self.instance.zuschlag_id:
                surcharge_qs = Surcharge.objects.filter(pk=self.instance.zuschlag_id) | surcharge_qs

        self.fields["leistung"].queryset = service_qs.distinct()
        self.fields["verschmutzungsgrad"].queryset = soiling_qs.distinct()
        self.fields["zuschlag"].queryset = surcharge_qs.distinct()
        self.fields["zuschlag"].required = False
        self.fields["einheit"].required = False
        self.fields["einheit"].initial = self.fields["einheit"].initial or "Einheit"
        self.fields["menge"].initial = self.fields["menge"].initial or 1


class BaseOfferItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_forms = [
            form
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False) and form.cleaned_data.get("leistung")
        ]
        if not active_forms:
            raise ValidationError("Bitte mindestens eine Leistungsposition anlegen.")


OfferItemFormSet = inlineformset_factory(
    Offer,
    OfferItem,
    form=OfferItemForm,
    formset=BaseOfferItemFormSet,
    extra=5,
    can_delete=True,
)
