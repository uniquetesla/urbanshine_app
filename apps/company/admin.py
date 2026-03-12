from django.contrib import admin

from .models import CompanySettings, OrderType, Price, Service, SoilingLevel, Surcharge


admin.site.register(Service)
admin.site.register(Price)
admin.site.register(OrderType)
admin.site.register(SoilingLevel)
admin.site.register(Surcharge)
admin.site.register(CompanySettings)
