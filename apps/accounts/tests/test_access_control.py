from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User, UserRole


class AccessControlTest(TestCase):
    def test_dashboard_redirects_anonymous_users_to_login(self):
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}")

    def test_dashboard_redirects_stammkunde_to_portal(self):
        user = User.objects.create_user(
            username="kunde-dashboard",
            password="testpass123",
            role=UserRole.STAMMKUNDE,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:dashboard"))

        self.assertRedirects(response, reverse("portal:dashboard"))

    def test_portal_redirects_anonymous_users_to_login(self):
        response = self.client.get(reverse("portal:dashboard"))

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('portal:dashboard')}")

    def test_employee_only_views_redirect_anonymous_users_to_login(self):
        response = self.client.get(reverse("orders:order_create"))

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('orders:order_create')}")
