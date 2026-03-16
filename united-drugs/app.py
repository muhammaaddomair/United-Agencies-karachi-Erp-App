import tkinter as tk
from db.database import init_db, migrate_db, ensure_default_users
from ui.login import LoginWindow


def main():
    init_db()
    migrate_db()
    ensure_default_users()

    root = tk.Tk()
    # Let UI decide size; allow maximize/minimize
    root.title("United Agencies karachi")
    root.geometry("1100x700")
    root.minsize(900, 600)

    LoginWindow(root)

    root.mainloop()


if __name__ == "__main__":
    main()
