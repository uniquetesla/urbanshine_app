from django.contrib import admin

from .models import Order, OrderAttachment, OrderPosition


class OrderPositionInline(admin.TabularInline):
    model = OrderPosition
    extra = 0


class OrderAttachmentInline(admin.TabularInline):
    model = OrderAttachment
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("auftragsnummer", "kunde", "auftragsart", "status", "termin", "gesamtpreis", "gesamtzeit_minuten")
    search_fields = ("auftragsnummer", "kunde__vorname", "kunde__nachname", "auftragsart")
    list_filter = ("status", "order_type")
    filter_horizontal = ("mitarbeiter",)
    inlines = [OrderPositionInline, OrderAttachmentInline]


@admin.register(OrderPosition)
class OrderPositionAdmin(admin.ModelAdmin):
    list_display = ("auftrag", "leistung", "einheit", "status", "einzelpreis", "geschaetzte_dauer_minuten")
    list_filter = ("status", "leistung", "verschmutzungsgrad", "einheit")


@admin.register(OrderAttachment)
class OrderAttachmentAdmin(admin.ModelAdmin):
    list_display = ("auftrag", "display_name", "uploaded_by", "uploaded_at")
