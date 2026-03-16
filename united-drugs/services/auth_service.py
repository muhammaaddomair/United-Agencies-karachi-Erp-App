import bcrypt
from db.database import get_connection


def authenticate(username, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT password, role FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    if not bcrypt.checkpw(password.encode(), row[0]):
        return None

    role = row[1] or "user"
    return role
