from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, UserRole
from apps.core.models import ActivityLog, ActivitySubject
from apps.customers.models import Customer
from apps.invoices.models import Invoice, PaymentStatus
from apps.orders.models import Order, OrderStatus


class DashboardMetricsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dash", password="testpass123", role=UserRole.CHEF)
        self.customer = Customer.objects.create(
            vorname="Max",
            nachname="Muster",
            strasse="Testweg",
            hausnummer="1",
            plz="12345",
            ort="Berlin",
            email="max@example.com",
        )

    def test_dashboard_uses_real_data(self):
        order = Order.objects.create(
            kunde=self.customer,
            auftragsart="Innenraum",
            leistungen="Test",
            preisberechnung="100",
            gesamtpreis=Decimal("100.00"),
            status=OrderStatus.IN_BEARBEITUNG,
        )
        Invoice.objects.create(kunde=self.customer, auftrag=order, betrag=Decimal("100.00"), zahlungsstatus=PaymentStatus.OFFEN)
        Invoice.objects.create(
            kunde=self.customer,
            betrag=Decimal("200.00"),
            zahlungsstatus=PaymentStatus.BEZAHLT,
            rechnungsdatum=timezone.localdate(),
        )
        ActivityLog.objects.create(
            actor=self.user,
            subject_type=ActivitySubject.AUFTRAG,
            subject_label="Auftrag #1",
            action="Auftrag erstellt",
            icon="🧽",
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aktive Aufträge")
        self.assertContains(response, "1")
        self.assertContains(response, "200.00")
        self.assertContains(response, "Auftrag #1")
