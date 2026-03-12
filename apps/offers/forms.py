from django import forms
from django.forms import inlineformset_factory

from .models import Offer, OfferItem


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ["kunde", "titel", "beschreibung", "rabatt_prozent", "status"]
        widgets = {
            "beschreibung": forms.Textarea(attrs={"rows": 3}),
        }


class OfferItemForm(forms.ModelForm):
    class Meta:
        model = OfferItem
        fields = ["bezeichnung", "menge", "einzelpreis"]


OfferItemFormSet = inlineformset_factory(
    Offer,
    OfferItem,
    form=OfferItemForm,
    extra=1,
    can_delete=True,
)
