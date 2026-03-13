from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.company.models import OrderType, Service, SoilingLevel, Surcharge
from apps.customers.models import Customer
from apps.orders.models import Order


class OrderCreateFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="pass123", role=UserRole.ADMIN)
        self.client.force_login(self.user)

        self.customer = Customer.objects.create(
            vorname="Max",
            nachname="Muster",
            strasse="Teststraße",
            hausnummer="1",
            plz="12345",
            ort="Musterstadt",
            email="max@example.com",
        )
        self.order_type = OrderType.objects.create(name="Innenraum", is_active=True)
        self.service = Service.objects.create(name="Sitze reinigen", price="100.00", estimated_duration_minutes=60, is_active=True)
        self.soiling = SoilingLevel.objects.create(name="Stark", multiplier="1.50", is_active=True)
        self.surcharge = Surcharge.objects.create(name="Express", amount="10.00", is_percentage=False, is_active=True)

    def _base_payload(self):
        return {
            "kunden_suche": f"{self.customer.kundennummer} · {self.customer.vorname} {self.customer.nachname}",
            "order_type": self.order_type.pk,
            "status": "neu",
            "termin": "",
            "interne_notizen": "",
            "orderposition_set-TOTAL_FORMS": "5",
            "orderposition_set-INITIAL_FORMS": "0",
            "orderposition_set-MIN_NUM_FORMS": "0",
            "orderposition_set-MAX_NUM_FORMS": "1000",
            "orderposition_set-0-leistung": str(self.service.pk),
            "orderposition_set-0-verschmutzungsgrad": str(self.soiling.pk),
            "orderposition_set-0-zuschlag": str(self.surcharge.pk),
            "orderposition_set-0-status": "neu",
        }

    def test_create_order_persists_and_redirects(self):
        response = self.client.post(reverse("orders:order_create"), data=self._base_payload(), follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.first()
        self.assertEqual(order.kunde, self.customer)
        self.assertEqual(order.gesamtpreis, self.service.price * self.soiling.multiplier + self.surcharge.amount)

    def test_create_order_shows_visible_error_when_customer_invalid(self):
        payload = self._base_payload()
        payload["kunden_suche"] = "unbekannt"

        response = self.client.post(reverse("orders:order_create"), data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kunde wurde nicht gefunden")
        self.assertContains(response, "Auftrag konnte nicht gespeichert werden")
        self.assertEqual(Order.objects.count(), 0)
