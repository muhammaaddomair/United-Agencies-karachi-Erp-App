from datetime import datetime
from db.database import get_connection


def list_services():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, price, created_at
        FROM services
        ORDER BY name COLLATE NOCASE ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_service_usage_count(service_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM invoices
        WHERE service_type = ?
    """, (service_name,))
    count = cur.fetchone()[0]
    conn.close()
    return count


def add_service(name, price):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO services (name, price, created_at)
        VALUES (?, ?, ?)
    """, (name, price, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def update_service(service_id, name, price):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE services
        SET name = ?, price = ?
        WHERE id = ?
    """, (name, price, service_id))
    conn.commit()
    conn.close()


def delete_service(service_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM services WHERE id = ?", (service_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    name = row[0]
    cur.execute("DELETE FROM services WHERE id = ?", (service_id,))
    conn.commit()
    conn.close()
    return name
