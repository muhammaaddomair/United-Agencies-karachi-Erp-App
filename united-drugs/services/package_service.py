from datetime import datetime
from db.database import get_connection


def list_packages():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.name, p.created_at, COALESCE(p.price, 0) AS total
        FROM packages p
        ORDER BY p.name COLLATE NOCASE ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_package_items(package_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, service_name
        FROM package_items
        WHERE package_id = ?
        ORDER BY id ASC
    """, (package_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def add_package(name, package_price, items):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO packages (name, price, created_at)
        VALUES (?, ?, ?)
    """, (name, package_price, datetime.now().isoformat()))
    package_id = cur.lastrowid

    for service_name in items:
        cur.execute("""
            INSERT INTO package_items (package_id, service_name)
            VALUES (?, ?)
        """, (package_id, service_name))

    conn.commit()
    conn.close()


def update_package(package_id, name, package_price, items):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE packages
        SET name = ?, price = ?
        WHERE id = ?
    """, (name, package_price, package_id))

    cur.execute("DELETE FROM package_items WHERE package_id = ?", (package_id,))

    for service_name in items:
        cur.execute("""
            INSERT INTO package_items (package_id, service_name)
            VALUES (?, ?)
        """, (package_id, service_name))

    conn.commit()
    conn.close()


def delete_package(package_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM package_items WHERE package_id = ?", (package_id,))
    cur.execute("DELETE FROM packages WHERE id = ?", (package_id,))
    conn.commit()
    conn.close()


def get_package_usage_count(package_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM invoices
        WHERE service_type LIKE ? OR service_type LIKE ?
    """, (f"%[Package] {package_name}%", f"%[Package] {package_name} - %"))
    count = cur.fetchone()[0]
    conn.close()
    return count
