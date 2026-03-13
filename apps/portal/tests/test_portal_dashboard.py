from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.customers.models import Customer
from apps.invoices.models import Invoice
from apps.offers.models import Offer
from apps.orders.models import Order
from apps.portal.models import AppointmentRequest


class CustomerPortalDashboardTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="kunde",
            password="testpass123",
            email="kunde@example.com",
            role=UserRole.STAMMKUNDE,
        )
        self.customer = Customer.objects.create(
            vorname="Max",
            nachname="Muster",
            strasse="Hauptstraße",
            hausnummer="1",
            plz="12345",
            ort="Berlin",
            email="kunde@example.com",
        )
        self.other_customer = Customer.objects.create(
            vorname="Eva",
            nachname="Extern",
            strasse="Nebenstraße",
            hausnummer="2",
            plz="54321",
            ort="Hamburg",
            email="extern@example.com",
        )

        self.order = Order.objects.create(
            kunde=self.customer,
            auftragsart="Innenreinigung",
            leistungen="Komplettpaket",
            preisberechnung="Pauschal",
            gesamtpreis=199,
        )
        Order.objects.create(
            kunde=self.other_customer,
            auftragsart="Lackpflege",
            leistungen="Premium",
            preisberechnung="Pauschal",
            gesamtpreis=299,
        )

        self.invoice = Invoice.objects.create(kunde=self.customer, auftrag=self.order, betrag=199)
        Invoice.objects.create(kunde=self.other_customer, betrag=300)

        Offer.objects.create(kunde=self.customer, titel="Angebot Stammkunde")
        Offer.objects.create(kunde=self.other_customer, titel="Angebot Fremd")

    def test_dashboard_shows_only_customer_owned_data(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("portal:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Angebot Stammkunde")
        self.assertNotContains(response, "Angebot Fremd")
        self.assertContains(response, f"R-{self.invoice.rechnungsnummer:05d}")
        self.assertContains(response, f"#{self.order.auftragsnummer}")

    def test_appointment_request_can_be_created(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("portal:dashboard"),
            {
                "name": "Max Muster",
                "email": "kunde@example.com",
                "telefon": "0123456",
                "wunschtermin_datum": date.today().isoformat(),
                "wunschtermin_uhrzeit": time(10, 30).isoformat(),
                "nachricht": "Bitte morgens",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AppointmentRequest.objects.count(), 1)
        self.assertContains(response, "Terminanfrage wurde erfolgreich gesendet")
