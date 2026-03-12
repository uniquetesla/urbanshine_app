from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from apps.orders.models import Order


class AppointmentOverviewView(LoginRequiredMixin, TemplateView):
    template_name = "scheduling/appointment_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.localtime()
        selected_view = self.request.GET.get("ansicht", "heute")
        if selected_view not in {"heute", "woche"}:
            selected_view = "heute"

        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        start_of_week = start_of_day - timedelta(days=start_of_day.weekday())
        end_of_week = start_of_week + timedelta(days=7)

        today_appointments = self._load_appointments(start_of_day, end_of_day)
        week_appointments = self._load_appointments(start_of_week, end_of_week)

        context.update(
            {
                "selected_view": selected_view,
                "today_appointments": today_appointments,
                "week_appointments": week_appointments,
            }
        )
        return context

    @staticmethod
    def _load_appointments(start, end):
        return (
            Order.objects.filter(termin__isnull=False, termin__gte=start, termin__lt=end)
            .select_related("kunde")
            .prefetch_related("mitarbeiter")
            .order_by("termin", "auftragsnummer")
        )
