from datetime import datetime
from db.database import get_connection


def list_vouchers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, code, discount_type, discount_value, created_at
        FROM vouchers
        ORDER BY code COLLATE NOCASE ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def add_voucher(code, discount_type, discount_value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO vouchers (code, discount_type, discount_value, created_at)
        VALUES (?, ?, ?, ?)
    """, (code, discount_type, discount_value, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def update_voucher(voucher_id, code, discount_type, discount_value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE vouchers
        SET code = ?, discount_type = ?, discount_value = ?
        WHERE id = ?
    """, (code, discount_type, discount_value, voucher_id))
    conn.commit()
    conn.close()


def delete_voucher(voucher_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM vouchers WHERE id = ?", (voucher_id,))
    conn.commit()
    conn.close()
