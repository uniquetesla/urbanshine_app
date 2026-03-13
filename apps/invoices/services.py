from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from apps.checkout.models import Sale
from apps.company.models import CompanySettings
from apps.orders.models import Order, OrderStatus

from .models import Invoice, InvoiceLineItem, PaymentStatus


def create_invoice_for_completed_order(order: Order) -> Invoice | None:
    if order.status != OrderStatus.ABGESCHLOSSEN:
        return None

    settings = CompanySettings.objects.first()
    if settings and not settings.invoice_generation_enabled:
        return None

    invoice = Invoice.objects.filter(auftrag=order).first()
    if not invoice:
        with transaction.atomic():
            invoice = Invoice.objects.create(
                kunde=order.kunde,
                auftrag=order,
                betrag=order.gesamtpreis,
                notizen="Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.",
            )
            _create_line_items_for_order(invoice, order)

    if not invoice.pdf_datei:
        _build_invoice_pdf(invoice, settings)
    return invoice


def create_manual_invoice_for_order(order: Order) -> Invoice:
    settings = CompanySettings.objects.first()
    invoice = Invoice.objects.filter(auftrag=order).first()
    if invoice:
        return invoice

    with transaction.atomic():
        invoice = Invoice.objects.create(
            kunde=order.kunde,
            auftrag=order,
            betrag=order.gesamtpreis,
            notizen="Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.",
        )
        _create_line_items_for_order(invoice, order)
    _build_invoice_pdf(invoice, settings)
    return invoice


def create_invoice_for_sale(sale: Sale) -> Invoice | None:
    if not sale.kunde:
        return None

    settings = CompanySettings.objects.first()
    invoice = Invoice.objects.filter(verkauf=sale).first()
    if invoice:
        return invoice

    with transaction.atomic():
        invoice = Invoice.objects.create(
            kunde=sale.kunde,
            verkauf=sale,
            betrag=sale.gesamtbetrag,
            notizen=f"Kassenverkauf #{sale.verkaufsnummer}",
        )
        _create_line_items_for_sale(invoice, sale)
    _build_invoice_pdf(invoice, settings)
    return invoice


def mark_invoice_as_paid(invoice: Invoice, paid_date=None):
    if invoice.zahlungsstatus == PaymentStatus.BEZAHLT:
        return False
    invoice.zahlungsstatus = PaymentStatus.BEZAHLT
    invoice.bezahlt_am = paid_date or timezone.localdate()
    invoice.save(update_fields=["zahlungsstatus", "bezahlt_am", "updated_at"])
    return True


def _create_line_items_for_order(invoice: Invoice, order: Order):
    if invoice.positionen.exists():
        return

    positions = order.positionen.select_related("leistung", "zuschlag", "verschmutzungsgrad")
    for index, pos in enumerate(positions, start=1):
        base_amount = (pos.leistung.price * pos.verschmutzungsgrad.multiplier).quantize(Decimal("0.01"))
        suffix = f" ({pos.verschmutzungsgrad.name})" if pos.verschmutzungsgrad else ""
        main_item = InvoiceLineItem.objects.create(
            rechnung=invoice,
            beschreibung=f"{pos.leistung.name}{suffix}",
            menge=Decimal("1.00"),
            einheit=pos.einheit or pos.leistung.unit or "Einheit",
            einzelpreis=base_amount,
            gesamtpreis=base_amount,
            sortierung=index,
            positionscode=str(index),
        )
        if pos.zuschlag and pos.zuschlag.amount > 0:
            surcharge_amount = _surcharge_amount_for_position(pos)
            InvoiceLineItem.objects.create(
                rechnung=invoice,
                parent=main_item,
                beschreibung=pos.zuschlag.name,
                menge=Decimal("1.00"),
                einheit="Position",
                einzelpreis=surcharge_amount,
                gesamtpreis=surcharge_amount,
                sortierung=(index * 100) + 1,
                positionscode=f"{index}.1",
            )


def _create_line_items_for_sale(invoice: Invoice, sale: Sale):
    if invoice.positionen.exists():
        return

    line_items = [
        InvoiceLineItem(
            rechnung=invoice,
            beschreibung=pos.artikel.name,
            menge=pos.menge,
            einheit=pos.artikel.einheit or "Stück",
            einzelpreis=pos.einzelpreis,
            gesamtpreis=pos.gesamtpreis,
            sortierung=index,
            positionscode=str(index),
        )
        for index, pos in enumerate(sale.positionen.select_related("artikel"), start=1)
    ]
    InvoiceLineItem.objects.bulk_create(line_items)


def _surcharge_amount_for_position(position):
    base = position.leistung.price * position.verschmutzungsgrad.multiplier
    if position.zuschlag.is_percentage:
        return ((base * position.zuschlag.amount) / Decimal("100")).quantize(Decimal("0.01"))
    return position.zuschlag.amount.quantize(Decimal("0.01"))


def _format_euro(value: Decimal) -> str:
    amount = Decimal(value).quantize(Decimal("0.01"))
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"


def _format_quantity(value: Decimal) -> str:
    number = Decimal(value).quantize(Decimal("0.01"))
    formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted


def _draw_footer(pdf, width, company_settings: CompanySettings | None):
    footer_y = 17 * mm
    col_width = (width - 30 * mm) / 3
    left_x = 15 * mm
    middle_x = left_x + col_width
    right_x = middle_x + col_width

    company_name = company_settings.company_name if company_settings else "UrbanShine"
    company_address_lines = (company_settings.address.splitlines() if company_settings and company_settings.address else [])

    pdf.setStrokeColor(colors.HexColor("#cccccc"))
    pdf.line(15 * mm, footer_y + 22 * mm, width - 15 * mm, footer_y + 22 * mm)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(left_x, footer_y + 17 * mm, "Unternehmen")
    pdf.drawString(middle_x, footer_y + 17 * mm, "Kontakt")
    pdf.drawString(right_x, footer_y + 17 * mm, "Bankverbindung")

    pdf.setFont("Helvetica", 8)
    y = footer_y + 13 * mm
    for line in [company_name, *company_address_lines[:2], f"Steuer-ID: {company_settings.tax_id}" if company_settings and company_settings.tax_id else ""]:
        if line:
            pdf.drawString(left_x, y, line)
            y -= 4 * mm

    y = footer_y + 13 * mm
    contact_lines = [
        f"Tel.: {company_settings.phone}" if company_settings and company_settings.phone else "",
        f"E-Mail: {company_settings.email}" if company_settings and company_settings.email else "",
        f"Web: {company_settings.website}" if company_settings and company_settings.website else "",
    ]
    for line in contact_lines:
        if line:
            pdf.drawString(middle_x, y, line)
            y -= 4 * mm

    y = footer_y + 13 * mm
    bank_lines = [
        company_settings.bank_name if company_settings and company_settings.bank_name else "",
        f"IBAN: {company_settings.iban}" if company_settings and company_settings.iban else "",
        f"BIC: {company_settings.bic}" if company_settings and company_settings.bic else "",
    ]
    for line in bank_lines:
        if line:
            pdf.drawString(right_x, y, line)
            y -= 4 * mm


def _build_invoice_pdf(invoice: Invoice, company_settings: CompanySettings | None):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    company_name = company_settings.company_name if company_settings else "UrbanShine"
    customer = invoice.kunde

    left_x = 20 * mm
    content_width = width - 40 * mm
    top_y = height - 20 * mm

    pdf.setTitle(f"Rechnung {invoice.formatted_rechnungsnummer}")

    if company_settings and company_settings.logo:
        logo_path = Path(company_settings.logo.path)
        if logo_path.exists():
            pdf.drawImage(
                str(logo_path),
                left_x,
                top_y - 15 * mm,
                width=32 * mm,
                height=15 * mm,
                preserveAspectRatio=True,
                anchor="nw",
                mask="auto",
            )

    y = top_y - 18 * mm
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left_x, y, company_name)
    pdf.setFont("Helvetica", 9)
    sender_lines = [
        *(company_settings.address.splitlines() if company_settings and company_settings.address else []),
        f"Steuer-ID: {company_settings.tax_id}" if company_settings and company_settings.tax_id else "",
        f"Tel.: {company_settings.phone}" if company_settings and company_settings.phone else "",
        f"E-Mail: {company_settings.email}" if company_settings and company_settings.email else "",
        f"Web: {company_settings.website}" if company_settings and company_settings.website else "",
    ]
    for line in sender_lines:
        if line:
            y -= 4.2 * mm
            pdf.drawString(left_x, y, line)

    address_y = top_y - 55 * mm
    pdf.setFont("Helvetica", 10)
    receiver_lines = [
        f"{customer.vorname} {customer.nachname}",
        f"{customer.strasse} {customer.hausnummer}",
        f"{customer.plz} {customer.ort}",
    ]
    for line in receiver_lines:
        pdf.drawString(left_x, address_y, line)
        address_y -= 5 * mm

    info_x = width - 82 * mm
    info_y = top_y - 40 * mm
    leistungsdatum = invoice.auftrag.termin.date() if invoice.auftrag and invoice.auftrag.termin else invoice.rechnungsdatum
    invoice_info = [
        ("Rechnungsdatum:", f"{invoice.rechnungsdatum:%d.%m.%Y}"),
        ("Rechnung Nr.:", invoice.formatted_rechnungsnummer),
        ("Leistungsdatum:", f"{leistungsdatum:%d.%m.%Y}"),
        ("Kundennummer:", customer.formatted_kundennummer),
    ]
    pdf.setFont("Helvetica", 9)
    for label, value in invoice_info:
        pdf.drawString(info_x, info_y, label)
        pdf.drawRightString(width - 20 * mm, info_y, value)
        info_y -= 5.2 * mm

    title_y = top_y - 83 * mm
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(left_x, title_y, "RECHNUNG")

    salutation = "Sehr geehrte Damen und Herren"
    if customer.nachname:
        salutation = f"Sehr geehrte/r {customer.vorname} {customer.nachname}"

    intro_y = title_y - 9 * mm
    pdf.setFont("Helvetica", 10)
    pdf.drawString(left_x, intro_y, f"{salutation},")
    intro_y -= 6 * mm
    pdf.drawString(left_x, intro_y, "wie vereinbart stelle ich Ihnen folgende Leistungen in Rechnung:")

    table_y = intro_y - 10 * mm
    row_height = 7 * mm

    col_pos_w = 12 * mm
    col_qty_w = 20 * mm
    col_unit_w = 24 * mm
    col_price_w = 26 * mm
    col_total_w = 28 * mm
    col_desc_w = content_width - (col_pos_w + col_qty_w + col_unit_w + col_price_w + col_total_w)

    col_pos_x = left_x
    col_qty_x = col_pos_x + col_pos_w
    col_unit_x = col_qty_x + col_qty_w
    col_desc_x = col_unit_x + col_unit_w
    col_price_x = col_desc_x + col_desc_w
    col_total_x = col_price_x + col_price_w

    def draw_header(y_pos):
        pdf.setFillColor(colors.HexColor("#f1f3f5"))
        pdf.rect(left_x, y_pos, content_width, row_height, fill=1, stroke=0)
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold", 8.5)
        pdf.drawString(col_pos_x + 1.2 * mm, y_pos + 2.3 * mm, "Pos.")
        pdf.drawRightString(col_qty_x + col_qty_w - 1.1 * mm, y_pos + 2.3 * mm, "Menge")
        pdf.drawString(col_unit_x + 1.0 * mm, y_pos + 2.3 * mm, "Einheit")
        pdf.drawString(col_desc_x + 1.0 * mm, y_pos + 2.3 * mm, "Beschreibung")
        pdf.drawRightString(col_price_x + col_price_w - 1.0 * mm, y_pos + 2.3 * mm, "Einzelpreis")
        pdf.drawRightString(col_total_x + col_total_w - 1.0 * mm, y_pos + 2.3 * mm, "Gesamtpreis")

    draw_header(table_y)

    y = table_y - 5.5 * mm
    pdf.setFont("Helvetica", 8.7)
    line_height = 4.1 * mm

    for item in invoice.positionen.select_related("parent").all():
        prefix = item.positionscode or "-"
        description = f"↳ {item.beschreibung}" if item.parent_id else item.beschreibung
        desc_lines = simpleSplit(description, "Helvetica", 8.7, col_desc_w - 2 * mm) or [""]
        unit_lines = simpleSplit(item.einheit or "", "Helvetica", 8.7, col_unit_w - 2 * mm) or [""]
        row_lines = max(len(desc_lines), len(unit_lines))
        row_bottom = y - ((row_lines - 1) * line_height)

        if row_bottom <= 55 * mm:
            _draw_footer(pdf, width, company_settings)
            pdf.showPage()
            y = height - 30 * mm
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(left_x, y, f"Rechnung {invoice.formatted_rechnungsnummer} – Fortsetzung")
            y -= 8 * mm
            draw_header(y)
            y -= 5.5 * mm
            pdf.setFont("Helvetica", 8.7)
            row_bottom = y - ((row_lines - 1) * line_height)

        pdf.drawRightString(col_pos_x + col_pos_w - 1.0 * mm, y, prefix)
        pdf.drawRightString(col_qty_x + col_qty_w - 1.0 * mm, y, _format_quantity(item.menge))
        for line_index in range(row_lines):
            if line_index < len(unit_lines):
                pdf.drawString(col_unit_x + 1.0 * mm, y - line_index * line_height, unit_lines[line_index])
            if line_index < len(desc_lines):
                pdf.drawString(col_desc_x + 1.0 * mm, y - line_index * line_height, desc_lines[line_index])

        pdf.drawRightString(col_price_x + col_price_w - 1.0 * mm, y, _format_euro(item.einzelpreis))
        pdf.drawRightString(col_total_x + col_total_w - 1.0 * mm, y, _format_euro(item.gesamtpreis))
        pdf.setStrokeColor(colors.HexColor("#e3e3e3"))
        pdf.line(left_x, row_bottom - 1.8 * mm, left_x + content_width, row_bottom - 1.8 * mm)
        y = row_bottom - 4.4 * mm

    y -= 4 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(width - 20 * mm, y, f"Rechnungsbetrag: {_format_euro(invoice.betrag)}")

    y -= 8 * mm
    pdf.setFont("Helvetica", 9)
    pdf.drawString(left_x, y, "Bitte überweisen Sie den Rechnungsbetrag innerhalb von 14 Tagen auf das unten angegebene Konto.")

    if company_settings is None or company_settings.kleinunternehmerregelung:
        y -= 6 * mm
        pdf.drawString(left_x, y, "Bitte beachten Sie, dass nach § 19 UStG keine Umsatzsteuer ausgewiesen wird.")

    y -= 10 * mm
    pdf.drawString(left_x, y, "Freundliche Grüße")
    y -= 6 * mm
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left_x, y, company_name)

    _draw_footer(pdf, width, company_settings)
    pdf.showPage()
    pdf.save()

    filename = f"rechnung_{invoice.formatted_rechnungsnummer}.pdf"
    invoice.pdf_datei.save(filename, ContentFile(buffer.getvalue()), save=True)
    buffer.close()
