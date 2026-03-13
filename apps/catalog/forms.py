from django import forms

from .models import Article, GoodsReceipt


class ArticleForm(forms.ModelForm):
    barcode = forms.CharField(label="Barcode", max_length=64, required=True)

    class Meta:
        model = Article
        fields = ["barcode", "name", "preis", "lagerbestand", "kategorie", "icon", "beschreibung"]
        widgets = {
            "beschreibung": forms.Textarea(attrs={"rows": 4}),
        }


class GoodsReceiptForm(forms.Form):
    barcode = forms.CharField(label="Barcode", max_length=64, widget=forms.TextInput(attrs={"autofocus": "autofocus"}))
    menge = forms.IntegerField(label="Menge", min_value=1, initial=1)
    notiz = forms.CharField(label="Notiz", required=False, max_length=255)

    def clean_barcode(self):
        return self.cleaned_data["barcode"].strip()
