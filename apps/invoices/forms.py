from django import forms
from django.utils import timezone


class MarkInvoicePaidForm(forms.Form):
    bezahlt_am = forms.DateField(
        required=False,
        label="Bezahlt am",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean_bezahlt_am(self):
        paid_date = self.cleaned_data.get("bezahlt_am")
        if paid_date and paid_date > timezone.localdate():
            raise forms.ValidationError("Das Bezahldatum darf nicht in der Zukunft liegen.")
        return paid_date
