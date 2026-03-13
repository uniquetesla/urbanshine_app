from django.contrib import admin

from .models import Invoice, InvoiceLineItem


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("rechnungsnummer", "kunde", "betrag", "zahlungsstatus", "rechnungsdatum", "faellig_am", "bezahlt_am")
    list_filter = ("zahlungsstatus", "rechnungsdatum", "bezahlt_am")
    search_fields = ("rechnungsnummer", "kunde__vorname", "kunde__nachname", "kunde__kundennummer")
    inlines = [InvoiceLineItemInline]
