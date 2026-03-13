from django import forms
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import ProtectedError

from apps.accounts.models import UserRole


class AdminChefRequiredMixin(UserPassesTestMixin):
    """Erlaubt Zugriff nur für Admin und Chef."""

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in {UserRole.ADMIN, UserRole.CHEF}


class DeleteConfirmationForm(forms.Form):
    current_password = forms.CharField(
        label="Passwort bestätigen",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    error_messages = {
        "invalid_password": "Das eingegebene Passwort ist nicht korrekt.",
    }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        password = self.cleaned_data["current_password"]
        if not self.user or not self.user.check_password(password):
            raise forms.ValidationError(self.error_messages["invalid_password"])
        return password


class PasswordProtectedDeleteMixin(AdminChefRequiredMixin):
    """Delete-Mixin mit Passwort-Sicherheitsabfrage und sauberem Fehlerhandling."""

    confirmation_form_class = DeleteConfirmationForm
    success_message = "Datensatz wurde gelöscht."
    protected_error_message = "Datensatz kann wegen bestehender Verknüpfungen nicht gelöscht werden."

    def get_confirmation_form(self):
        return self.confirmation_form_class(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("confirmation_form", self.get_confirmation_form())
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        confirmation_form = self.confirmation_form_class(request.POST, user=request.user)
        if not confirmation_form.is_valid():
            return self.render_to_response(self.get_context_data(object=self.object, confirmation_form=confirmation_form))

        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            from django.contrib import messages
            from django.shortcuts import redirect

            messages.error(request, self.protected_error_message)
            return redirect(self.get_success_url())
