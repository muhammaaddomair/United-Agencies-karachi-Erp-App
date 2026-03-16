from datetime import datetime

from db.database import get_connection


def save_invoice(invoice_data, products):
    """
    Saves invoice header + line items and deducts selected quantities from inventory.
    invoice_data: dict of new form fields
    products: list[dict] with keys: inventory_item_id, product_description, quantity, unit_price
    """
    if not products:
        raise ValueError("Please select at least one product.")

    conn = get_connection()
    try:
        cur = conn.cursor()

        # Validate stock before any write.
        for item in products:
            item_id = int(item["inventory_item_id"])
            qty = float(item["quantity"])
            cur.execute("SELECT quantity FROM inventory_items WHERE id = ?", (item_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("A selected product no longer exists in inventory.")
            available = float(row[0] or 0)
            if qty <= 0:
                raise ValueError("Selected product quantity must be greater than zero.")
            if qty > available:
                raise ValueError(f"Insufficient stock for product ID {item_id}. Available: {available:,.2f}")

        created_at = datetime.now().isoformat()
        bill_no = invoice_data.get("bill_no", "").strip()
        to_text = invoice_data.get("to_text", "").strip()
        total_qty = sum(float(item["quantity"]) for item in products)

        cur.execute(
            """
            INSERT INTO invoices (
                invoice_no,
                customer_name,
                total,
                created_at,
                service_type,
                phone,
                paid_amount,
                payment_mode,
                str_no,
                ntn_no,
                bill_no,
                delivery_challan_no,
                order_contract_no,
                order_date,
                inspection_note_no,
                invoice_date,
                to_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bill_no,
                to_text.splitlines()[0] if to_text else "",
                total_qty,
                created_at,
                ", ".join(item.get("product_description", "") for item in products),
                "",
                0.0,
                "",
                invoice_data.get("str_no", "").strip(),
                invoice_data.get("ntn_no", "").strip(),
                bill_no,
                invoice_data.get("delivery_challan_no", "").strip(),
                invoice_data.get("order_contract_no", "").strip(),
                invoice_data.get("order_date", "").strip(),
                invoice_data.get("inspection_note_no", "").strip(),
                invoice_data.get("invoice_date", "").strip(),
                to_text,
            ),
        )
        invoice_id = cur.lastrowid

        for item in products:
            item_id = int(item["inventory_item_id"])
            qty = float(item["quantity"])
            unit_price = float(item.get("unit_price", 0.0))
            desc = item.get("product_description", "")

            cur.execute(
                """
                INSERT INTO invoice_items (
                    invoice_id,
                    inventory_item_id,
                    product_description,
                    quantity,
                    unit_price
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (invoice_id, item_id, desc, qty, unit_price),
            )
            cur.execute(
                "UPDATE inventory_items SET quantity = quantity - ? WHERE id = ?",
                (qty, item_id),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_invoices():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id,
            bill_no,
            str_no,
            ntn_no,
            to_text,
            invoice_date,
            order_date,
            total,
            created_at
        FROM invoices
        ORDER BY datetime(created_at) DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows
