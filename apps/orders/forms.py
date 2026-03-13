from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from apps.accounts.models import UserRole
from apps.company.models import OrderType, Service, SoilingLevel, Surcharge
from apps.customers.models import Customer
from apps.core.number_sequences import parse_sequence_value

from .models import Order, OrderPosition


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class OrderForm(forms.ModelForm):
    kunden_suche = forms.CharField(label="Kunde suchen", required=True)
    bilder = forms.FileField(required=False, widget=MultiFileInput(attrs={"multiple": True}), label="Dateien Upload")

    class Meta:
        model = Order
        fields = ["kunde", "order_type", "status", "termin", "mitarbeiter", "interne_notizen"]
        widgets = {
            "interne_notizen": forms.Textarea(attrs={"rows": 4}),
            "termin": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "mitarbeiter": forms.SelectMultiple(attrs={"size": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["kunde"].widget = forms.HiddenInput()
        self.fields["kunde"].required = False
        self.fields["order_type"].queryset = OrderType.objects.filter(is_active=True)
        self.fields["mitarbeiter"].queryset = self.fields["mitarbeiter"].queryset.filter(
            role__in=[UserRole.ADMIN, UserRole.CHEF, UserRole.MITARBEITER]
        )
        self.customer_suggestions = [
            f"{customer.formatted_kundennummer} · {customer.vorname} {customer.nachname}"
            for customer in Customer.objects.order_by("nachname", "vorname")
        ]
        if self.instance and self.instance.pk:
            self.fields["kunden_suche"].initial = (
                f"{self.instance.kunde.formatted_kundennummer} · " f"{self.instance.kunde.vorname} {self.instance.kunde.nachname}"
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

    def clean_bilder(self):
        return self.files.getlist("bilder")


class OrderPositionForm(forms.ModelForm):
    class Meta:
        model = OrderPosition
        fields = ["leistung", "verschmutzungsgrad", "zuschlag", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        leistung_qs = Service.objects.filter(is_active=True)
        soiling_qs = SoilingLevel.objects.filter(is_active=True)
        surcharge_qs = Surcharge.objects.filter(is_active=True)

        if self.instance and self.instance.pk:
            leistung_qs = Service.objects.filter(pk=self.instance.leistung_id) | leistung_qs
            soiling_qs = SoilingLevel.objects.filter(pk=self.instance.verschmutzungsgrad_id) | soiling_qs
            if self.instance.zuschlag_id:
                surcharge_qs = Surcharge.objects.filter(pk=self.instance.zuschlag_id) | surcharge_qs

        self.fields["leistung"].queryset = leistung_qs.distinct()
        self.fields["verschmutzungsgrad"].queryset = soiling_qs.distinct()
        self.fields["zuschlag"].queryset = surcharge_qs.distinct()
        self.fields["zuschlag"].required = False


class BaseOrderPositionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_forms = [
            form
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False) and form.cleaned_data.get("leistung")
        ]
        if not active_forms:
            raise ValidationError("Bitte mindestens eine Leistungsposition anlegen.")


OrderPositionFormSet = inlineformset_factory(
    Order,
    OrderPosition,
    form=OrderPositionForm,
    formset=BaseOrderPositionFormSet,
    extra=5,
    can_delete=True,
)
