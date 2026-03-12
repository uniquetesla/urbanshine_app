from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, TemplateView, View

from apps.accounts.models import User, UserRole
from apps.orders.models import Order


class EmployeeAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = (UserRole.ADMIN, UserRole.CHEF, UserRole.MITARBEITER)

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in self.allowed_roles


class EmployeeListView(EmployeeAccessMixin, ListView):
    model = User
    template_name = "employees/employee_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        queryset = (
            User.objects.filter(role__in=[UserRole.ADMIN, UserRole.CHEF, UserRole.MITARBEITER], is_active=True)
            .order_by("first_name", "last_name", "username")
            .prefetch_related(
                Prefetch(
                    "auftraege",
                    queryset=Order.objects.select_related("kunde").order_by("termin", "auftragsnummer"),
                )
            )
        )
        if self.request.user.role == UserRole.MITARBEITER:
            return queryset.filter(pk=self.request.user.pk)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role == UserRole.MITARBEITER:
            context["unassigned_orders"] = Order.objects.none()
            return context

        context["unassigned_orders"] = (
            Order.objects.filter(mitarbeiter__isnull=True)
            .select_related("kunde")
            .order_by("termin", "auftragsnummer")
            .distinct()
        )
        return context


class EmployeeDetailView(EmployeeAccessMixin, DetailView):
    model = User
    template_name = "employees/employee_detail.html"
    context_object_name = "employee"

    def get_queryset(self):
        queryset = User.objects.filter(role__in=[UserRole.ADMIN, UserRole.CHEF, UserRole.MITARBEITER], is_active=True)
        if self.request.user.role == UserRole.MITARBEITER:
            return queryset.filter(pk=self.request.user.pk)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee_orders = (
            self.object.auftraege.select_related("kunde")
            .prefetch_related("mitarbeiter")
            .order_by("termin", "auftragsnummer")
        )
        calendar = defaultdict(list)
        for order in employee_orders:
            date_label = order.termin.strftime("%d.%m.%Y") if order.termin else "Ohne Termin"
            calendar[date_label].append(order)

        context["employee_orders"] = employee_orders
        context["calendar_items"] = dict(calendar)
        if self.request.user.role == UserRole.MITARBEITER:
            context["unassigned_orders"] = Order.objects.none()
            return context

        context["unassigned_orders"] = (
            Order.objects.filter(mitarbeiter__isnull=True)
            .select_related("kunde")
            .order_by("termin", "auftragsnummer")
            .distinct()
        )
        return context


class EmployeeCalendarView(EmployeeAccessMixin, TemplateView):
    template_name = "employees/employee_calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = User.objects.filter(role__in=[UserRole.ADMIN, UserRole.CHEF, UserRole.MITARBEITER], is_active=True)
        if self.request.user.role == UserRole.MITARBEITER:
            queryset = queryset.filter(pk=self.request.user.pk)

        employee = get_object_or_404(queryset, pk=self.kwargs["pk"])
        employee_orders = employee.auftraege.select_related("kunde").order_by("termin", "auftragsnummer")

        calendar = defaultdict(list)
        for order in employee_orders:
            date_label = order.termin.strftime("%d.%m.%Y") if order.termin else "Ohne Termin"
            calendar[date_label].append(order)

        context["employee"] = employee
        context["calendar_items"] = dict(calendar)
        context["employee_orders"] = employee_orders
        return context


class AssignOrdersView(EmployeeAccessMixin, View):
    allowed_roles = (UserRole.ADMIN, UserRole.CHEF)
    success_url = reverse_lazy("employees:employee_list")

    def post(self, request, pk):
        employee = get_object_or_404(
            User.objects.filter(role__in=[UserRole.ADMIN, UserRole.CHEF, UserRole.MITARBEITER], is_active=True),
            pk=pk,
        )
        order_ids = request.POST.getlist("order_ids")
        if not order_ids:
            messages.warning(request, "Bitte mindestens einen Auftrag auswählen.")
            return redirect("employees:employee_detail", pk=employee.pk)

        orders = Order.objects.filter(pk__in=order_ids)
        for order in orders:
            order.mitarbeiter.add(employee)

        messages.success(request, f"{orders.count()} Auftrag/Aufträge wurde(n) {employee.get_full_name() or employee.username} zugewiesen.")
        return redirect("employees:employee_detail", pk=employee.pk)
