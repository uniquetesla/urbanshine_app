from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, UserCreationForm

from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Benutzername",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Benutzername"}),
    )
    password = forms.CharField(
        label="Passwort",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Passwort"}),
    )


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "is_active")
        labels = {
            "username": "Benutzername",
            "first_name": "Vorname",
            "last_name": "Nachname",
            "email": "E-Mail",
            "role": "Rolle",
            "is_active": "Aktiv",
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "role", "is_active")
        labels = {
            "first_name": "Vorname",
            "last_name": "Nachname",
            "email": "E-Mail",
            "role": "Rolle",
            "is_active": "Aktiv",
        }


class AdminUserPasswordResetForm(SetPasswordForm):
    """Passwort-Neuvergabe durch berechtigte interne Benutzer."""

    new_password1 = forms.CharField(
        label="Neues Passwort",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    new_password2 = forms.CharField(
        label="Neues Passwort bestätigen",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
