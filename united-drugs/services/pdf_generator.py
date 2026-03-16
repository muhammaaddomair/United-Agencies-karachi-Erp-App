import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from utils.paths import get_invoices_dir


def generate_invoice_pdf(invoice_no, customer, service, phone, paid_amount):
    invoices_dir = get_invoices_dir()

    filename = f"{invoice_no}.pdf"
    filepath = os.path.join(invoices_dir, filename)
    c = canvas.Canvas(filepath, pagesize=A4)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 800, "United Agencies karachi Invoice")

    c.setFont("Helvetica", 12)
    c.drawString(50, 765, f"Invoice No: {invoice_no}")
    c.drawString(50, 745, f"Customer: {customer}")
    c.drawString(50, 725, f"Service: {service}")
    if phone:
        c.drawString(50, 705, f"Phone: {phone}")

    c.drawString(50, 675, f"Date: {datetime.now().strftime('%d-%m-%Y')}")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 640, f"Paid Amount: {paid_amount:,.2f}")

    c.showPage()
    c.save()
    return filepath
