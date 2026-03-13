from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User, UserRole


class DocumentAccessTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin_docs", password="testpass123", role=UserRole.ADMIN)
        self.employee = User.objects.create_user(username="emp_docs", password="testpass123", role=UserRole.MITARBEITER)

    def test_documents_visible_for_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(response, reverse("documents:document_list"))

    def test_documents_forbidden_for_employee(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse("documents:document_list"))
        self.assertEqual(response.status_code, 403)
