import tkinter as tk
from PIL import Image, ImageTk
from services.auth_service import authenticate
from utils.paths import get_asset_path
from ui.dashboard import DashboardWindow
from ui.theme import COLORS, FONTS, SPACING, get_button_style, get_input_style


class LoginWindow:
    def __init__(self, root):
        self.root = root

        root.title("United Agencies karachi - Login")
        root.configure(bg=COLORS["bg"])
        root.minsize(900, 600)

        # Responsive layout
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        self._build()

    def _clear_root(self):
        for w in self.root.winfo_children():
            w.destroy()

    def _build(self):
        container = tk.Frame(self.root, bg=COLORS["bg"])
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Centered card (keeps your UI)
        outer = tk.Frame(container, bg=COLORS["border"])
        outer.place(relx=0.5, rely=0.5, anchor="center")

        card = tk.Frame(outer, bg=COLORS["card"])
        card.pack(padx=2, pady=2)

        content = tk.Frame(card, bg=COLORS["card"])
        content.pack(padx=52, pady=52)

        # Display Logo
        try:
            logo_path = get_asset_path("logo.png")
            logo_image = Image.open(logo_path)
            logo_image.thumbnail((200, 200), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            tk.Label(
                content,
                image=self.logo_photo,
                bg=COLORS["card"]
            ).pack(pady=(0, SPACING["lg"]))
        except Exception as e:
            # Fallback if logo not found
            print(f"Logo not found: {e}")

        tk.Label(
            content,
            text="Sign in to continue",
            font=FONTS["body"],
            fg=COLORS["text_medium"],
            bg=COLORS["card"]
        ).pack(pady=(SPACING["sm"], SPACING["xl"]))

        tk.Label(content, text="Username", font=FONTS["label"], fg=COLORS["text_medium"], bg=COLORS["card"]).pack(anchor="w")
        self.username = tk.Entry(content, **get_input_style())
        self.username.insert(0, "admin")
        self.username.pack(fill="x", ipady=10, pady=(SPACING["xs"], SPACING["lg"]))

        tk.Label(content, text="Password", font=FONTS["label"], fg=COLORS["text_medium"], bg=COLORS["card"]).pack(anchor="w")
        self.password = tk.Entry(content, show="â€¢", **get_input_style())
        self.password.pack(fill="x", ipady=10, pady=(SPACING["xs"], SPACING["lg"]))

        self.error = tk.Label(content, text="", font=FONTS["small"], fg=COLORS["error"], bg=COLORS["card"])
        self.error.pack(pady=(0, SPACING["md"]))

        btn_style = get_button_style("primary")
        self.login_btn = tk.Button(content, text="Sign In", command=self._login, **btn_style)
        self.login_btn.pack(fill="x", ipady=6)

        self.root.bind("<Return>", lambda e: self._login())

    def _login(self):
        u = self.username.get().strip()
        p = self.password.get()

        if not u or not p:
            self.error.config(text="Please enter both username and password")
            return

        role = authenticate(u, p)
        if role:
            self._clear_root()
            DashboardWindow(self.root, role=role)
            return

        self.error.config(text="Invalid username or password")

