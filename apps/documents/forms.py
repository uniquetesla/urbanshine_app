from django import forms

from .models import CompanyDocument


class CompanyDocumentForm(forms.ModelForm):
    class Meta:
        model = CompanyDocument
        fields = ["title", "description", "category", "file"]
