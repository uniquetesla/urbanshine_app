from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, FormView, ListView, TemplateView, UpdateView, View

from apps.core.models import ActivityLog
from apps.invoices.models import Invoice, PaymentStatus
from apps.orders.models import Order, OrderStatus
from apps.core.security import PasswordProtectedDeleteMixin

from .forms import AdminUserPasswordResetForm, LoginForm, UserCreateForm, UserUpdateForm
from .models import User, UserRole


class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles = ()

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in self.allowed_roles


class UrbanShineLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.role == UserRole.STAMMKUNDE:
            from django.shortcuts import redirect

            return redirect("portal:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        context["active_orders"] = Order.objects.exclude(status__in=[OrderStatus.ABGESCHLOSSEN, OrderStatus.ABGERECHNET, OrderStatus.STORNIERT]).count()
        open_invoices = Invoice.objects.filter(zahlungsstatus__in=[PaymentStatus.OFFEN, PaymentStatus.UEBERFAELLIG, PaymentStatus.TEILWEISE_BEZAHLT])
        context["open_invoices_count"] = open_invoices.count()
        context["open_invoices_sum"] = open_invoices.aggregate(total=Sum("betrag"))["total"] or 0
        context["month_revenue"] = Invoice.objects.filter(rechnungsdatum__gte=month_start, zahlungsstatus=PaymentStatus.BEZAHLT).aggregate(total=Sum("betrag"))["total"] or 0
        context["year_revenue"] = Invoice.objects.filter(rechnungsdatum__gte=year_start, zahlungsstatus=PaymentStatus.BEZAHLT).aggregate(total=Sum("betrag"))["total"] or 0
        context["latest_activities"] = ActivityLog.objects.select_related("actor")[:15]
        return context


class UserManagementAccessMixin(LoginRequiredMixin, RoleRequiredMixin):
    allowed_roles = (UserRole.ADMIN, UserRole.CHEF)


class UserListView(UserManagementAccessMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    queryset = User.objects.order_by("username")


class UserCreateView(UserManagementAccessMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")
    allowed_roles = (UserRole.ADMIN,)

    def form_valid(self, form):
        messages.success(self.request, "Benutzer wurde erfolgreich erstellt.")
        return super().form_valid(form)


class UserUpdateView(UserManagementAccessMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")
    allowed_roles = (UserRole.ADMIN,)

    def form_valid(self, form):
        messages.success(self.request, "Benutzer wurde erfolgreich aktualisiert.")
        return super().form_valid(form)


class UserDeactivateView(UserManagementAccessMixin, View):
    allowed_roles = (UserRole.ADMIN,)

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, "Sie können Ihr eigenes Konto nicht deaktivieren.")
            return HttpResponseRedirect(reverse_lazy("accounts:user_list"))

        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.success(request, f"Benutzer {user.username} wurde deaktiviert.")
        return HttpResponseRedirect(reverse_lazy("accounts:user_list"))


class UserPasswordResetView(UserManagementAccessMixin, FormView):
    template_name = "accounts/user_password_reset.html"
    form_class = AdminUserPasswordResetForm
    success_url = reverse_lazy("accounts:user_list")

    def dispatch(self, request, *args, **kwargs):
        self.target_user = get_object_or_404(User, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.target_user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["target_user"] = self.target_user
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f"Passwort für {self.target_user.username} wurde erfolgreich neu gesetzt.")
        return super().form_valid(form)


class UserDeleteView(PasswordProtectedDeleteMixin, DeleteView):
    model = User
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("accounts:user_list")
    success_message = "Benutzer wurde dauerhaft gelöscht."
    protected_error_message = "Benutzer kann nicht gelöscht werden, weil verknüpfte Pflichtdaten existieren."

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object == request.user:
            messages.error(request, "Sie können Ihr eigenes Konto nicht löschen.")
            return HttpResponseRedirect(reverse_lazy("accounts:user_list"))
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, self.success_message)
        return response


class LogoutView(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        messages.success(request, "Sie wurden erfolgreich abgemeldet.")
        return HttpResponseRedirect(reverse_lazy("accounts:login"))
