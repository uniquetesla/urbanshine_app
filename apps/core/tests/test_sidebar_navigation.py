from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User, UserRole


class SidebarNavigationLinksTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="navtester",
            password="testpass123",
            role=UserRole.ADMIN,
        )

    def test_sidebar_links_for_employees_and_appointments_are_real_routes(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/mitarbeiter/"')
        self.assertContains(response, 'href="/termine/"')
        self.assertNotContains(response, '>Mitarbeiter</a>\n            <a href="#"')
