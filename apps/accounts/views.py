from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, View

from .forms import LoginForm, UserCreateForm, UserUpdateForm
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


class LogoutView(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        messages.success(request, "Sie wurden erfolgreich abgemeldet.")
        return HttpResponseRedirect(reverse_lazy("accounts:login"))
