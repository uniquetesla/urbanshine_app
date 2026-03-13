from django.contrib import admin

from .models import ActivityLog, NumberSequence


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("subject_type", "subject_label", "action", "actor", "created_at")
    list_filter = ("subject_type", "created_at")
    search_fields = ("subject_label", "action", "details")


@admin.register(NumberSequence)
class NumberSequenceAdmin(admin.ModelAdmin):
    list_display = ("sequence_type", "prefix", "separator", "start_value", "padding", "last_value", "updated_at")
    list_editable = ("prefix", "separator", "start_value", "padding", "last_value")
