from django.apps import apps
from django.contrib.auth.hashers import make_password
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def ensure_default_admin(sender, **kwargs):
    if sender.label != "accounts":
        return

    user_model = apps.get_model("accounts", "User")
    user_model.objects.update_or_create(
        username="admin",
        defaults={
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
            "role": "admin",
            "password": make_password("admin1234"),
            "email": "admin@urbanshine.local",
            "first_name": "Admin",
            "last_name": "UrbanShine",
        },
    )
