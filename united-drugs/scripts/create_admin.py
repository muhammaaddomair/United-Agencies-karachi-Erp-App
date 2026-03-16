import bcrypt
from db.database import init_db, migrate_db, get_connection

init_db()
migrate_db()

conn = get_connection()
cur = conn.cursor()

hashed = bcrypt.hashpw("myadmin786".encode(), bcrypt.gensalt())

cur.execute("""
INSERT OR IGNORE INTO users (username, password, role)
VALUES (?, ?, ?)
""", ("admin", hashed, "admin"))
cur.execute("UPDATE users SET password=?, role=? WHERE username=?", (hashed, "admin", "admin"))

conn.commit()
conn.close()

print("✅ Admin user created")
print("Username: admin")
print("Password: myadmin786")
