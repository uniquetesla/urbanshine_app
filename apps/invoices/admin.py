from django.contrib import admin

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("rechnungsnummer", "kunde", "betrag", "zahlungsstatus", "rechnungsdatum", "faellig_am")
    list_filter = ("zahlungsstatus", "rechnungsdatum")
    search_fields = ("rechnungsnummer", "kunde__vorname", "kunde__nachname", "kunde__kundennummer")
