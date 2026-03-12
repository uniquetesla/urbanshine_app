from django.contrib import admin

from .models import Order, OrderImage


class OrderImageInline(admin.TabularInline):
    model = OrderImage
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("auftragsnummer", "kunde", "auftragsart", "status", "termin", "gesamtpreis")
    search_fields = ("auftragsnummer", "kunde__vorname", "kunde__nachname", "auftragsart")
    list_filter = ("status", "verschmutzungsgrad")
    filter_horizontal = ("mitarbeiter",)
    inlines = [OrderImageInline]


@admin.register(OrderImage)
class OrderImageAdmin(admin.ModelAdmin):
    list_display = ("auftrag", "uploaded_at")
