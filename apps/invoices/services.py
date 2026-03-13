from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from apps.checkout.models import Sale
from apps.company.models import CompanySettings
from apps.orders.models import Order, OrderStatus

from .models import Invoice


def create_invoice_for_completed_order(order: Order) -> Invoice | None:
    if order.status != OrderStatus.ABGESCHLOSSEN:
        return None

    settings = CompanySettings.objects.first()
    if settings and not settings.invoice_generation_enabled:
        return None

    invoice = Invoice.objects.filter(auftrag=order).first()
    if not invoice:
        invoice = Invoice.objects.create(
            kunde=order.kunde,
            auftrag=order,
            betrag=order.gesamtpreis,
            notizen="Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.",
        )

    if not invoice.pdf_datei:
        _build_invoice_pdf(invoice, settings)
    return invoice


def create_manual_invoice_for_order(order: Order) -> Invoice:
    settings = CompanySettings.objects.first()
    invoice = Invoice.objects.filter(auftrag=order).first()
    if invoice:
        return invoice

    invoice = Invoice.objects.create(
        kunde=order.kunde,
        auftrag=order,
        betrag=order.gesamtpreis,
        notizen="Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.",
    )
    _build_invoice_pdf(invoice, settings)
    return invoice


def create_invoice_for_sale(sale: Sale) -> Invoice | None:
    if not sale.kunde:
        return None

    settings = CompanySettings.objects.first()
    invoice = Invoice.objects.filter(verkauf=sale).first()
    if invoice:
        return invoice

    notes = [f"Kassenverkauf #{sale.verkaufsnummer}", "Positionen:"]
    for pos in sale.positionen.select_related("artikel"):
        notes.append(f"- {pos.artikel.name}: {pos.menge} × {pos.einzelpreis} € = {pos.gesamtpreis} €")

    invoice = Invoice.objects.create(
        kunde=sale.kunde,
        verkauf=sale,
        betrag=sale.gesamtbetrag,
        notizen="\n".join(notes),
    )
    _build_invoice_pdf(invoice, settings)
    return invoice


def _build_invoice_pdf(invoice: Invoice, company_settings: CompanySettings | None):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 25 * mm
    if company_settings and company_settings.logo:
        logo_path = Path(company_settings.logo.path)
        if logo_path.exists():
            pdf.drawImage(str(logo_path), 15 * mm, y - 15 * mm, width=35 * mm, height=15 * mm, preserveAspectRatio=True)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawRightString(width - 15 * mm, y, f"Rechnung {invoice.formatted_rechnungsnummer}")

    y -= 20 * mm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(15 * mm, y, "Firmendaten")
    pdf.setFont("Helvetica", 10)
    company_name = company_settings.company_name if company_settings else "UrbanShine"
    company_address = company_settings.address if company_settings else ""
    company_phone = company_settings.phone if company_settings else ""
    company_email = company_settings.email if company_settings else ""
    for line in [company_name, *company_address.splitlines(), company_phone, company_email]:
        if line:
            y -= 5 * mm
            pdf.drawString(15 * mm, y, line)

    customer = invoice.kunde
    y_customer = height - 55 * mm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(110 * mm, y_customer, "Kundenadresse")
    pdf.setFont("Helvetica", 10)
    for line in [
        f"{customer.vorname} {customer.nachname}",
        f"{customer.strasse} {customer.hausnummer}",
        f"{customer.plz} {customer.ort}",
    ]:
        y_customer -= 5 * mm
        pdf.drawString(110 * mm, y_customer, line)

    y -= 12 * mm
    pdf.setFont("Helvetica", 10)
    pdf.drawString(15 * mm, y, f"Rechnungsdatum: {invoice.rechnungsdatum:%d.%m.%Y}")
    y -= 6 * mm
    if invoice.auftrag:
        pdf.drawString(15 * mm, y, f"Auftrag: {invoice.auftrag.formatted_auftragsnummer}")
    elif invoice.verkauf:
        pdf.drawString(15 * mm, y, f"Verkauf: {invoice.verkauf.verkaufsnummer}")

    y -= 10 * mm
    pdf.setFillColor(colors.HexColor("#f2f2f2"))
    pdf.rect(15 * mm, y, width - 30 * mm, 8 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(18 * mm, y + 3 * mm, "Position")
    pdf.drawRightString(width - 18 * mm, y + 3 * mm, "Betrag")

    y -= 10 * mm
    pdf.setFont("Helvetica", 10)
    if invoice.auftrag:
        position_text = invoice.auftrag.auftragsart
    elif invoice.verkauf:
        position_text = f"Kassenverkauf #{invoice.verkauf.verkaufsnummer}"
    else:
        position_text = "Leistung"
    pdf.drawString(18 * mm, y, position_text)
    pdf.drawRightString(width - 18 * mm, y, f"{invoice.betrag:.2f} €")

    y -= 10 * mm
    if invoice.auftrag:
        details = invoice.auftrag.leistungen[:95]
        pdf.setFillColor(colors.HexColor("#555555"))
        pdf.drawString(18 * mm, y, details)
        pdf.setFillColor(colors.black)

    y -= 16 * mm
    pdf.line(15 * mm, y, width - 15 * mm, y)
    y -= 8 * mm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(18 * mm, y, "Summe")
    pdf.drawRightString(width - 18 * mm, y, f"{invoice.betrag:.2f} €")

    y -= 7 * mm
    pdf.setFont("Helvetica", 9)
    pdf.drawRightString(width - 18 * mm, y, "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.")

    y -= 18 * mm
    pdf.setFont("Helvetica", 9)
    pdf.drawString(15 * mm, y, f"Erstellt am {timezone.localtime():%d.%m.%Y %H:%M}")

    pdf.showPage()
    pdf.save()

    filename = f"rechnung_{invoice.formatted_rechnungsnummer}.pdf"
    invoice.pdf_datei.save(filename, ContentFile(buffer.getvalue()), save=True)
    buffer.close()
