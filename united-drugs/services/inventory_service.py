from datetime import datetime

from db.database import get_connection


def save_inventory_item(
    reg_no,
    batch_no,
    mfg_date,
    exp_date,
    quantity,
    product_description,
    trade_price,
    discount_percent,
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO inventory_items (
            reg_no,
            batch_no,
            mfg_date,
            exp_date,
            quantity,
            product_description,
            trade_price,
            discount_percent,
            price_per_unit,
            amount_pkr,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            reg_no,
            batch_no,
            mfg_date,
            exp_date,
            quantity,
            product_description,
            trade_price,
            discount_percent,
            0.0,
            0.0,
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def list_inventory_items():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id,
            reg_no,
            batch_no,
            mfg_date,
            exp_date,
            quantity,
            product_description,
            trade_price,
            discount_percent,
            created_at
        FROM inventory_items
        ORDER BY created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_inventory_item(
    item_id,
    reg_no,
    batch_no,
    mfg_date,
    exp_date,
    quantity,
    product_description,
    trade_price,
    discount_percent,
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE inventory_items
        SET
            reg_no = ?,
            batch_no = ?,
            mfg_date = ?,
            exp_date = ?,
            quantity = ?,
            product_description = ?,
            trade_price = ?,
            discount_percent = ?
        WHERE id = ?
        """,
        (
            reg_no,
            batch_no,
            mfg_date,
            exp_date,
            quantity,
            product_description,
            trade_price,
            discount_percent,
            item_id,
        ),
    )
    conn.commit()
    conn.close()
