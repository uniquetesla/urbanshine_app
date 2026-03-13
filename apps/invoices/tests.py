from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, UserRole
from apps.checkout.models import PaymentMethod, Sale, SaleItem
from apps.catalog.models import Article
from apps.company.models import Service, SoilingLevel, Surcharge
from apps.customers.models import Customer
from apps.invoices.models import Invoice, InvoiceLineItem, PaymentStatus
from apps.invoices.services import create_manual_invoice_for_order
from apps.orders.models import Order, OrderPosition


class InvoicePaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="pass123", role=UserRole.ADMIN)
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(
            vorname="Ina",
            nachname="Kunde",
            strasse="Musterweg",
            hausnummer="7",
            plz="11111",
            ort="Musterstadt",
            email="ina@example.com",
        )
        self.invoice = Invoice.objects.create(kunde=self.customer, betrag="99.00")

    def test_mark_invoice_paid_from_list(self):
        response = self.client.post(
            reverse("invoices:invoice_mark_paid", kwargs={"pk": self.invoice.pk}),
            data={"next": reverse("invoices:invoice_list")},
        )
        self.assertEqual(response.status_code, 302)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.zahlungsstatus, PaymentStatus.BEZAHLT)
        self.assertEqual(self.invoice.bezahlt_am, timezone.localdate())


class InvoiceLineItemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="chef", password="pass123", role=UserRole.ADMIN)
        self.customer = Customer.objects.create(
            vorname="Otto",
            nachname="Kunde",
            strasse="Allee",
            hausnummer="9",
            plz="22222",
            ort="Stadt",
            email="otto@example.com",
        )

    def test_order_invoice_creates_separate_line_items(self):
        service = Service.objects.create(name="Innenreinigung", price="80.00", estimated_duration_minutes=90)
        level = SoilingLevel.objects.create(name="Normal", multiplier="1.00")
        surcharge = Surcharge.objects.create(name="Tierhaar", amount="15.00", is_percentage=False)
        order = Order.objects.create(kunde=self.customer)
        OrderPosition.objects.create(auftrag=order, leistung=service, verschmutzungsgrad=level, zuschlag=surcharge)
        order.recalculate_totals(save=True)

        invoice = create_manual_invoice_for_order(order)
        self.assertGreaterEqual(invoice.positionen.count(), 2)
        self.assertTrue(invoice.positionen.filter(beschreibung__icontains="Innenreinigung").exists())
        self.assertTrue(invoice.positionen.filter(beschreibung__icontains="Zuschlag").exists())

    def test_sale_invoice_uses_article_line_items(self):
        article = Article.objects.create(
            name="Mikrofasertuch",
            kategorie="Zubehör",
            icon=Article.ICON_MIKROFASERTUCH,
            preis="5.00",
            lagerbestand=30,
        )
        sale = Sale.objects.create(mitarbeiter=self.user, kunde=self.customer, zahlungsart=PaymentMethod.RECHNUNG, gesamtbetrag="10.00")
        SaleItem.objects.create(verkauf=sale, artikel=article, menge=2, einzelpreis="5.00", gesamtpreis="10.00")

        from apps.invoices.services import create_invoice_for_sale

        invoice = create_invoice_for_sale(sale)
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.positionen.count(), 1)
        item = InvoiceLineItem.objects.get(rechnung=invoice)
        self.assertEqual(item.beschreibung, "Mikrofasertuch")
        self.assertEqual(item.menge, 2)
