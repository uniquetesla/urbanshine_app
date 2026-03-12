from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    CHEF = "chef", "Chef"
    MITARBEITER = "mitarbeiter", "Mitarbeiter"
    STAMMKUNDE = "stammkunde", "Stammkunde"


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STAMMKUNDE,
        verbose_name="Rolle",
    )

    class Meta:
        permissions = [
            ("can_manage_users", "Kann Benutzer verwalten"),
            ("can_change_roles", "Kann Rollen ändern"),
            ("can_deactivate_users", "Kann Benutzer deaktivieren"),
        ]

    @property
    def is_management(self):
        return self.role in {UserRole.ADMIN, UserRole.CHEF}

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
