from django import forms

from .models import Article


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ["name", "preis", "lagerbestand", "kategorie", "icon", "beschreibung"]
        widgets = {
            "beschreibung": forms.Textarea(attrs={"rows": 4}),
        }
