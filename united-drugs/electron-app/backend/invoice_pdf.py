import io
import json
import os
import sys
from datetime import datetime

from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from reportlab.pdfgen import canvas


APP_NAME = "United Agencies karachi"
COMPANY = "TechSaws"
TEMPLATE_NAME = "UA invoice template.pdf"
PAGE_WIDTH = 612
PAGE_HEIGHT = 1008


def get_repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_template_path():
    return os.path.join(get_repo_root(), "assets", TEMPLATE_NAME)


def get_invoices_dir():
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    path = os.path.join(docs, "UnitedAgenciesKarachiInvoices")
    os.makedirs(path, exist_ok=True)
    return path


def sanitize_filename(value: str):
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in (value or "invoice"))
    return safe.strip("._") or "invoice"


def format_date(value: str):
    if not value:
        return ""

    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return value


def format_number(value):
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0
    return f"{number:,.2f}"


def draw_text(pdf, x, y, text, *, font="Helvetica", size=11):
    pdf.setFont(font, size)
    pdf.drawString(x, y, str(text or ""))


def draw_multiline(pdf, x, y, text, *, font="Helvetica", size=11, line_gap=14):
    lines = [line.strip() for line in str(text or "").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return

    pdf.setFont(font, size)
    for index, line in enumerate(lines[:4]):
        pdf.drawString(x, y - (index * line_gap), line)


def wrap_text(text, max_chars):
    words = [word for word in str(text or "").split() if word]
    if not words:
        return []

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_wrapped_box(pdf, x, y, text, *, width_chars, max_lines, font="Helvetica", size=11, line_gap=12):
    lines = wrap_text(text, width_chars)[:max_lines]
    if not lines:
        return

    pdf.setFont(font, size)
    for index, line in enumerate(lines):
        pdf.drawString(x, y - (index * line_gap), line)


def build_overlay(payload):
    return {
        "fileNo": (72, 826, payload.get("fileNo", "")),
        "billNo": (74, 811, payload.get("billNo", "")),
        "deliveryChallanNo": (125, 795, payload.get("deliveryChallanNo", "")),
        "orderContractNo": (133, 779, payload.get("orderContractNo", "")),
        "orderDate": (104, 764, format_date(payload.get("orderDate", ""))),
        "inspectionNoteNo": (117, 749, payload.get("inspectionNoteNo", "")),
        "toText": (131, 726, payload.get("toText", "")),
        "invoiceDate": (452, 69, format_date(payload.get("invoiceDate", ""))),
    }


def generate_invoice_pdf(payload):
    template_path = get_template_path()
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Invoice template not found: {template_path}")

    filename = sanitize_filename(payload.get("billNo") or payload.get("fileNo") or "invoice")
    output_dir = payload.get("outputDir") or get_invoices_dir()
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{filename}.pdf")

    template_page = PdfReader(template_path).pages[0]
    template_obj = pagexobj(template_page)
    pdf = canvas.Canvas(output_path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    pdf.doForm(makerl(pdf, template_obj))

    field_positions = build_overlay(payload)
    draw_text(pdf, field_positions["fileNo"][0], field_positions["fileNo"][1], field_positions["fileNo"][2], size=12)
    draw_text(pdf, field_positions["billNo"][0], field_positions["billNo"][1], field_positions["billNo"][2], size=12)
    draw_text(
        pdf,
        field_positions["deliveryChallanNo"][0],
        field_positions["deliveryChallanNo"][1],
        field_positions["deliveryChallanNo"][2],
        size=12,
    )
    draw_text(
        pdf,
        field_positions["orderContractNo"][0],
        field_positions["orderContractNo"][1],
        field_positions["orderContractNo"][2],
        size=12,
    )
    draw_text(pdf, field_positions["orderDate"][0], field_positions["orderDate"][1], field_positions["orderDate"][2], size=12)
    draw_text(
        pdf,
        field_positions["inspectionNoteNo"][0],
        field_positions["inspectionNoteNo"][1],
        field_positions["inspectionNoteNo"][2],
        size=12,
    )
    draw_wrapped_box(
        pdf,
        field_positions["toText"][0],
        field_positions["toText"][1],
        field_positions["toText"][2],
        width_chars=70,
        max_lines=2,
        size=12,
        line_gap=14,
    )

    pdf.setFont("Helvetica", 9)
    row_top = 650
    row_height = 22
    for index, item in enumerate(payload.get("products", [])[:11]):
        y = row_top - (index * row_height)
        amount = float(item.get("quantity", 0) or 0) * float(item.get("unitPrice", 0) or 0)

        pdf.drawString(24, y - 2, str(item.get("regNo", "") or "")[:10])
        pdf.drawString(74, y, str(item.get("batchNo", "") or "")[:12])
        pdf.drawString(123, y - 2, format_date(item.get("mfgDate", "")))
        pdf.drawString(179, y, format_date(item.get("expDate", "")))
        pdf.drawRightString(282, y - 1, format_number(item.get("quantity", 0)))
        draw_wrapped_box(
            pdf,
            302,
            y + 1,
            item.get("productDescription", "") or "",
            width_chars=27,
            max_lines=2,
            size=9,
            line_gap=11,
        )
        pdf.drawRightString(516, y + 2, format_number(item.get("unitPrice", 0)))
        pdf.drawRightString(590, y + 2, format_number(amount))

    draw_text(
        pdf,
        field_positions["invoiceDate"][0],
        field_positions["invoiceDate"][1],
        field_positions["invoiceDate"][2],
        font="Helvetica-Bold",
        size=11,
    )
    pdf.save()
    return output_path


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: invoice_pdf.py <payload_json_path>")

    payload_path = sys.argv[1]
    with open(payload_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    output_path = generate_invoice_pdf(payload)
    print(json.dumps({"ok": True, "path": output_path}))


if __name__ == "__main__":
    main()
