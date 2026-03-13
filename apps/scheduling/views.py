from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone
from django.views.generic import TemplateView

from apps.orders.models import Order, OrderStatus


class AppointmentOverviewView(LoginRequiredMixin, TemplateView):
    template_name = "scheduling/appointment_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.localtime()
        selected_view = self.request.GET.get("ansicht", "tag")
        if selected_view not in {"tag", "woche"}:
            selected_view = "tag"

        selected_date = self._resolve_selected_date(now)
        start_of_day = selected_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        start_of_week = start_of_day - timedelta(days=start_of_day.weekday())
        end_of_week = start_of_week + timedelta(days=7)

        today_appointments = self._load_appointments(start_of_day, end_of_day)
        week_appointments = self._load_appointments(start_of_week, end_of_week)
        unassigned_orders = (
            Order.objects.filter(Q(termin__isnull=True) | Q(mitarbeiter__isnull=True), status__in=[OrderStatus.NEU, OrderStatus.GEPLANT])
            .select_related("kunde")
            .prefetch_related("mitarbeiter")
            .distinct()
            .order_by("-auftragsnummer")[:25]
        )

        context.update(
            {
                "selected_view": selected_view,
                "selected_date": selected_date,
                "today_appointments": today_appointments,
                "week_appointments": week_appointments,
                "unassigned_orders": unassigned_orders,
                "status_labels": dict(OrderStatus.choices),
            }
        )
        return context

    def _resolve_selected_date(self, now):
        date_raw = self.request.GET.get("datum")
        if not date_raw:
            return now
        try:
            selected = datetime.strptime(date_raw, "%Y-%m-%d")
            return timezone.make_aware(selected, timezone.get_current_timezone())
        except ValueError:
            return now

    @staticmethod
    def _load_appointments(start, end):
        return (
            Order.objects.filter(termin__isnull=False, termin__gte=start, termin__lt=end)
            .select_related("kunde")
            .prefetch_related("mitarbeiter")
            .order_by("termin", "auftragsnummer")
        )
