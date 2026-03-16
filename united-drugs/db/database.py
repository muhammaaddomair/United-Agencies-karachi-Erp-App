import os
import sqlite3
import bcrypt
from utils.paths import get_app_data_dir

DB_NAME = os.path.join(get_app_data_dir(), "database.db")


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Users table (bcrypt hashes stored as BLOB)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password BLOB,
        role TEXT DEFAULT 'user'
    )
    """)

    # Invoices table (initial minimal schema)
    # We'll migrate/alter to newer columns safely via migrate_db()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT,
        customer_name TEXT,
        total REAL,
        created_at TEXT,
        service_type TEXT,
        phone TEXT,
        paid_amount REAL,
        payment_mode TEXT,
        str_no TEXT,
        ntn_no TEXT,
        bill_no TEXT,
        delivery_challan_no TEXT,
        order_contract_no TEXT,
        order_date TEXT,
        inspection_note_no TEXT,
        invoice_date TEXT,
        to_text TEXT
    )
    """)

    # Services table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        price REAL,
        created_at TEXT
    )
    """)

    # Packages table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        price REAL DEFAULT 0,
        created_at TEXT
    )
    """)

    # Package items table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS package_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        package_id INTEGER,
        service_name TEXT,
        price REAL
    )
    """)

    # Vouchers table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vouchers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        discount_type TEXT,
        discount_value REAL,
        created_at TEXT
    )
    """)

    # Inventory items table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reg_no TEXT,
        batch_no TEXT,
        mfg_date TEXT,
        exp_date TEXT,
        quantity REAL,
        product_description TEXT,
        trade_price REAL,
        discount_percent REAL,
        price_per_unit REAL,
        amount_pkr REAL,
        created_at TEXT
    )
    """)

    # Invoice products/items table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        inventory_item_id INTEGER,
        product_description TEXT,
        quantity REAL,
        unit_price REAL
    )
    """)

    conn.commit()
    conn.close()


def migrate_db():
    """
    Safe, idempotent migration.
    Adds missing columns without deleting data.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Ensure users table exists (in case init_db wasn't run)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password BLOB,
        role TEXT DEFAULT 'user'
    )
    """)

    # Ensure invoices table exists (in case init_db wasn't run)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT,
        customer_name TEXT,
        total REAL,
        created_at TEXT,
        service_type TEXT,
        phone TEXT,
        paid_amount REAL,
        payment_mode TEXT,
        str_no TEXT,
        ntn_no TEXT,
        bill_no TEXT,
        delivery_challan_no TEXT,
        order_contract_no TEXT,
        order_date TEXT,
        inspection_note_no TEXT,
        invoice_date TEXT,
        to_text TEXT
    )
    """)

    # Ensure services table exists (in case init_db wasn't run)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        price REAL,
        created_at TEXT
    )
    """)

    # Ensure packages table exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        price REAL DEFAULT 0,
        created_at TEXT
    )
    """)

    # Ensure package items table exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS package_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        package_id INTEGER,
        service_name TEXT,
        price REAL
    )
    """)

    # Ensure vouchers table exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vouchers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        discount_type TEXT,
        discount_value REAL,
        created_at TEXT
    )
    """)

    # Ensure inventory items table exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reg_no TEXT,
        batch_no TEXT,
        mfg_date TEXT,
        exp_date TEXT,
        quantity REAL,
        product_description TEXT,
        trade_price REAL,
        discount_percent REAL,
        price_per_unit REAL,
        amount_pkr REAL,
        created_at TEXT
    )
    """)

    # Ensure invoice items table exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        inventory_item_id INTEGER,
        product_description TEXT,
        quantity REAL,
        unit_price REAL
    )
    """)

    cur.execute("PRAGMA table_info(invoices)")
    cols = {row[1] for row in cur.fetchall()}

    # New columns used by the current app
    if "service_type" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN service_type TEXT")

    if "phone" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN phone TEXT")

    if "paid_amount" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN paid_amount REAL")

    if "payment_mode" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN payment_mode TEXT")
    if "str_no" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN str_no TEXT")
    if "ntn_no" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN ntn_no TEXT")
    if "bill_no" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN bill_no TEXT")
    if "delivery_challan_no" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN delivery_challan_no TEXT")
    if "order_contract_no" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN order_contract_no TEXT")
    if "order_date" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN order_date TEXT")
    if "inspection_note_no" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN inspection_note_no TEXT")
    if "invoice_date" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN invoice_date TEXT")
    if "to_text" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN to_text TEXT")

    cur.execute("PRAGMA table_info(users)")
    user_cols = {row[1] for row in cur.fetchall()}

    if "role" not in user_cols:
        cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")

    cur.execute("PRAGMA table_info(packages)")
    package_cols = {row[1] for row in cur.fetchall()}
    if "price" not in package_cols:
        cur.execute("ALTER TABLE packages ADD COLUMN price REAL DEFAULT 0")

    # Ensure existing users have a default role
    cur.execute("UPDATE users SET role='user' WHERE role IS NULL OR role=''")
    # Promote built-in admin account if present
    cur.execute("UPDATE users SET role='admin' WHERE username='admin' AND role!='admin'")

    # Optional: keep "total" for backward compatibility (older invoices)
    # Not required by new UI, but harmless to keep.

    conn.commit()
    conn.close()


def ensure_default_users():
    """
    Ensure default admin/user accounts exist for first-time installs.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    has_admin = cur.fetchone()[0] > 0

    cur.execute("SELECT COUNT(*) FROM users WHERE username='user'")
    has_user = cur.fetchone()[0] > 0

    if not has_admin:
        admin_hash = bcrypt.hashpw("myadmin786".encode(), bcrypt.gensalt())
        cur.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, ("admin", admin_hash, "admin"))

    if not has_user:
        user_hash = bcrypt.hashpw("user123".encode(), bcrypt.gensalt())
        cur.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, ("user", user_hash, "user"))

    conn.commit()
    conn.close()
