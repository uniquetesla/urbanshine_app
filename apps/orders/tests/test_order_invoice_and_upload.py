from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.company.models import OrderType, Service, SoilingLevel
from apps.customers.models import Customer
from apps.invoices.models import Invoice
from apps.orders.models import Order, OrderAttachment, OrderStatus


class OrderUploadAndInvoiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin2", password="pass123", role=UserRole.ADMIN)
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(
            vorname="Erika",
            nachname="Mustermann",
            strasse="Teststraße",
            hausnummer="2",
            plz="12345",
            ort="Musterstadt",
            email="erika@example.com",
        )
        self.order_type = OrderType.objects.create(name="Außen", is_active=True)
        self.service = Service.objects.create(name="Handwäsche", price="50.00", estimated_duration_minutes=45, is_active=True)
        self.soiling = SoilingLevel.objects.create(name="Mittel", multiplier="1.20", is_active=True)

    def _payload(self):
        return {
            "kunden_suche": f"{self.customer.kundennummer} · {self.customer.vorname} {self.customer.nachname}",
            "order_type": self.order_type.pk,
            "status": OrderStatus.NEU,
            "termin": "",
            "interne_notizen": "",
            "orderposition_set-TOTAL_FORMS": "5",
            "orderposition_set-INITIAL_FORMS": "0",
            "orderposition_set-MIN_NUM_FORMS": "0",
            "orderposition_set-MAX_NUM_FORMS": "1000",
            "orderposition_set-0-leistung": str(self.service.pk),
            "orderposition_set-0-verschmutzungsgrad": str(self.soiling.pk),
            "orderposition_set-0-zuschlag": "",
            "orderposition_set-0-status": "neu",
        }

    def test_create_order_with_file_upload(self):
        file_obj = SimpleUploadedFile("foto.txt", b"upload-test", content_type="text/plain")
        payload = self._payload()
        payload["anhaenge"] = [file_obj]

        response = self.client.post(reverse("orders:order_create"), data=payload)

        self.assertEqual(response.status_code, 302)
        order = Order.objects.first()
        self.assertTrue(OrderAttachment.objects.filter(auftrag=order).exists())

    def test_manual_invoice_creation_from_order(self):
        order = Order.objects.create(kunde=self.customer, order_type=self.order_type, auftragsart="Außen", gesamtpreis="120.00")

        response = self.client.post(reverse("orders:order_create_invoice", kwargs={"pk": order.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Invoice.objects.filter(auftrag=order).count(), 1)

        self.client.post(reverse("orders:order_create_invoice", kwargs={"pk": order.pk}))
        self.assertEqual(Invoice.objects.filter(auftrag=order).count(), 1)
