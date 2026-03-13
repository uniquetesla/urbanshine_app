from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.catalog.models import Article
from apps.customers.models import Customer
from apps.invoices.models import Invoice
from apps.checkout.models import PaymentMethod, Sale, SaleItem


class CheckoutInvoiceFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="kasse", password="pass123", role=UserRole.ADMIN)
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(
            vorname="Karl",
            nachname="Kunde",
            strasse="Teststraße",
            hausnummer="3",
            plz="12345",
            ort="Musterstadt",
            email="karl@example.com",
        )

    def test_create_invoice_for_sale(self):
        article = Article.objects.create(name="Shampoo", kategorie="Pflege", preis="15.00", lagerbestand=20)
        sale = Sale.objects.create(mitarbeiter=self.user, kunde=self.customer, zahlungsart=PaymentMethod.RECHNUNG, gesamtbetrag="30.00")
        SaleItem.objects.create(verkauf=sale, artikel=article, menge=2, einzelpreis="15.00", gesamtpreis="30.00")

        response = self.client.post(reverse("checkout:sale_create_invoice", kwargs={"pk": sale.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Invoice.objects.filter(verkauf=sale).count(), 1)

        self.client.post(reverse("checkout:sale_create_invoice", kwargs={"pk": sale.pk}))
        self.assertEqual(Invoice.objects.filter(verkauf=sale).count(), 1)
