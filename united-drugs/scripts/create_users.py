import bcrypt
from db.database import init_db, migrate_db, get_connection


def main():
    init_db()
    migrate_db()

    conn = get_connection()
    cur = conn.cursor()

    admin_hash = bcrypt.hashpw("myadmin786".encode(), bcrypt.gensalt())
    user_hash = bcrypt.hashpw("user123".encode(), bcrypt.gensalt())

    cur.execute("""
    INSERT OR IGNORE INTO users (username, password, role)
    VALUES (?, ?, ?)
    """, ("admin", admin_hash, "admin"))
    cur.execute("UPDATE users SET password=?, role=? WHERE username=?", (admin_hash, "admin", "admin"))

    cur.execute("""
    INSERT OR IGNORE INTO users (username, password, role)
    VALUES (?, ?, ?)
    """, ("user", user_hash, "user"))
    cur.execute("UPDATE users SET password=?, role=? WHERE username=?", (user_hash, "user", "user"))

    conn.commit()
    conn.close()

    print("Admin user created")
    print("Username: admin")
    print("Password: myadmin786")
    print("User created")
    print("Username: user")
    print("Password: user123")


if __name__ == "__main__":
    main()
