import json
import os
import sqlite3
import sys

import bcrypt


def connect(db_path: str):
    directory = os.path.dirname(db_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    return sqlite3.connect(db_path)


def bootstrap(db_path: str):
    conn = connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password BLOB,
            role TEXT DEFAULT 'user'
        )
        """
    )

    cur.execute("PRAGMA table_info(users)")
    cols = {row[1] for row in cur.fetchall()}
    if "role" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")

    cur.execute("UPDATE users SET role='user' WHERE role IS NULL OR role=''")
    cur.execute("UPDATE users SET role='admin' WHERE username='admin' AND role!='admin'")

    cur.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", bcrypt.hashpw(b"myadmin786", bcrypt.gensalt()), "admin"),
        )

    cur.execute("SELECT COUNT(*) FROM users WHERE username='user'")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("user", bcrypt.hashpw(b"user123", bcrypt.gensalt()), "user"),
        )

    conn.commit()
    conn.close()
    print(json.dumps({"ok": True}))


def authenticate(db_path: str, username: str, password: str):
    conn = connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT password, role FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
      print(json.dumps({"ok": False, "role": None}))
      return

    if not bcrypt.checkpw(password.encode("utf-8"), row[0]):
      print(json.dumps({"ok": False, "role": None}))
      return

    print(json.dumps({"ok": True, "role": row[1] or "user"}))


def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: auth_helper.py <bootstrap|authenticate> <db_path> [args...]")

    command = sys.argv[1]
    db_path = sys.argv[2]

    if command == "bootstrap":
        bootstrap(db_path)
        return

    if command == "authenticate":
        if len(sys.argv) < 5:
            raise SystemExit("authenticate requires username and password")
        authenticate(db_path, sys.argv[3], sys.argv[4])
        return

    raise SystemExit(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
