import tkinter as tk
from tkinter import ttk
from datetime import datetime
from PIL import Image, ImageTk

from ui.invoice_form import InvoiceForm
from ui.inventory_form import InventoryForm
from services.invoice_service import list_invoices
from ui.theme import (
    COLORS,
    FONTS,
    SPACING,
    DIMENSIONS,
    apply_theme,
    create_zebra_table,
    get_button_style,
)
from utils.paths import get_asset_path


class DashboardWindow:
    def __init__(self, root, role):
        self.root = root
        self.role = role
        self.root.title("United Agencies karachi")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(1000, 600)

        apply_theme(self.root)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.shell = tk.Frame(self.root, bg=COLORS["bg"])
        self.shell.grid(row=0, column=0, sticky="nsew")
        self.shell.grid_rowconfigure(0, weight=1)
        self.shell.grid_columnconfigure(0, weight=0, minsize=DIMENSIONS["sidebar_width"])
        self.shell.grid_columnconfigure(1, weight=1)

        self._create_sidebar()
        self._create_main()
        self.show_invoices_tab()

    def _create_sidebar(self):
        self.sidebar = tk.Frame(self.shell, bg=COLORS["sidebar_dark"], width=DIMENSIONS["sidebar_width"])
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(0, weight=0)
        self.sidebar.grid_rowconfigure(1, weight=1)

        sidebar_content = tk.Frame(self.sidebar, bg=COLORS["sidebar_dark"])
        sidebar_content.grid(row=0, column=0, sticky="n")
        sidebar_content.grid_columnconfigure(0, weight=1)

        try:
            logo_path = get_asset_path("logo.png")
            logo_image = Image.open(logo_path)
            logo_image.thumbnail((230, 230), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            tk.Label(sidebar_content, image=self.logo_photo, bg=COLORS["sidebar_dark"]).pack(
                pady=(SPACING["xl"], SPACING["md"])
            )
        except Exception as e:
            print(f"Logo not found: {e}")
            tk.Label(
                sidebar_content,
                text="UA",
                font=("Segoe UI", 24, "bold"),
                bg=COLORS["sidebar_dark"],
                fg="white",
            ).pack(anchor="w", padx=(SPACING["md"], 0), pady=(SPACING["xl"], SPACING["md"]))

        divider = tk.Frame(sidebar_content, bg=COLORS["sidebar_border"], height=1)
        divider.pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["lg"]))

        nav = tk.Frame(sidebar_content, bg=COLORS["sidebar_dark"])
        nav.pack(fill="x", padx=SPACING["sm"])

        self.btn_new = tk.Button(
            nav,
            text="Invoices",
            font=FONTS["sidebar_menu"],
            bg=COLORS["sidebar_dark"],
            fg="white",
            relief="flat",
            anchor="w",
            padx=SPACING["md"],
            pady=SPACING["md"],
            command=self.show_invoices_tab,
        )
        self.btn_new.pack(fill="x", pady=SPACING["xs"])

        self.btn_inventory = tk.Button(
            nav,
            text="Inventory",
            font=FONTS["sidebar_menu"],
            bg=COLORS["sidebar_dark"],
            fg="white",
            relief="flat",
            anchor="w",
            padx=SPACING["md"],
            pady=SPACING["md"],
            command=self.show_inventory_form,
        )
        self.btn_inventory.pack(fill="x", pady=SPACING["xs"])

        bottom = tk.Frame(self.sidebar, bg=COLORS["sidebar_dark"])
        bottom.grid(row=1, column=0, sticky="s", pady=SPACING["xl"])
        tk.Button(
            bottom,
            text="Logout",
            font=FONTS["sidebar_menu"],
            bg=COLORS["sidebar_dark"],
            fg="white",
            relief="flat",
            anchor="w",
            padx=SPACING["md"],
            pady=SPACING["md"],
            command=self._logout,
        ).pack(fill="x", padx=SPACING["sm"])

        self.datetime_label = tk.Label(
            bottom,
            text="",
            font=FONTS["small"],
            bg=COLORS["sidebar_dark"],
            fg=COLORS["text_light"],
            justify="left",
            anchor="w",
        )
        self.datetime_label.pack(fill="x", padx=SPACING["sm"], pady=(SPACING["sm"], 0))
        self._update_sidebar_datetime()

    def _create_main(self):
        self.main = tk.Frame(self.shell, bg=COLORS["bg"])
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self.header = tk.Frame(self.main, bg=COLORS["card"], height=DIMENSIONS["header_height"])
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)

        self.header_title = tk.Label(
            self.header,
            text="Invoices",
            font=FONTS["page_title"],
            bg=COLORS["card"],
            fg=COLORS["text_dark"],
        )
        self.header_title.pack(side="left", padx=SPACING["xl"])

        border = tk.Frame(self.header, bg=COLORS["border"], height=1)
        border.pack(side="bottom", fill="x")

        self.content = tk.Frame(self.main, bg=COLORS["bg"])
        self.content.grid(row=1, column=0, sticky="nsew", padx=SPACING["xl"], pady=SPACING["xl"])
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _set_active_tab(self, active):
        default_bg = COLORS["sidebar_dark"]
        active_bg = COLORS["primary"]
        self.btn_new.config(bg=active_bg if active == "invoice" else default_bg)
        self.btn_inventory.config(bg=active_bg if active == "inventory" else default_bg)

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _logout(self):
        for w in self.root.winfo_children():
            w.destroy()
        from ui.login import LoginWindow

        LoginWindow(self.root)

    def show_invoices_tab(self):
        self._set_active_tab("invoice")
        self._clear_content()
        self.header_title.config(text="Invoices")

        root = tk.Frame(self.content, bg=COLORS["bg"])
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        top = tk.Frame(root, bg=COLORS["bg"])
        top.grid(row=0, column=0, sticky="ew", pady=(0, SPACING["md"]))
        tk.Button(top, text="Create Invoice", command=self._open_create_invoice_window, **get_button_style("primary")).pack(
            side="right"
        )

        card_outer = tk.Frame(root, bg=COLORS["border"])
        card_outer.grid(row=1, column=0, sticky="nsew")
        card_outer.grid_rowconfigure(0, weight=1)
        card_outer.grid_columnconfigure(0, weight=1)

        card = tk.Frame(card_outer, bg=COLORS["card"])
        card.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        table_wrap = tk.Frame(card, bg=COLORS["card"])
        table_wrap.grid(row=0, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")

        columns = ("Bill No", "STR No", "NTN No", "To", "Invoice Date", "Your Order Date", "Qty")
        self.invoice_table = ttk.Treeview(table_wrap, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        self.invoice_table.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.invoice_table.yview)

        widths = {
            "Bill No": 180,
            "STR No": 130,
            "NTN No": 130,
            "To": 260,
            "Invoice Date": 130,
            "Your Order Date": 160,
            "Qty": 90,
        }
        for col in columns:
            anchor = "e" if col == "Qty" else "w"
            self.invoice_table.heading(col, text=col, anchor=anchor)
            self.invoice_table.column(col, width=widths[col], minwidth=80, anchor=anchor)
        create_zebra_table(self.invoice_table)
        self._load_invoices()

    def show_inventory_form(self):
        self._set_active_tab("inventory")
        self._clear_content()
        self.header_title.config(text="Inventory")
        InventoryForm(self.content)

    def _open_create_invoice_window(self):
        win = tk.Toplevel(self.root)
        win.title("Create Invoice")
        win.configure(bg=COLORS["bg"])
        win.geometry("1280x860")
        win.minsize(1000, 700)
        win.transient(self.root)
        win.grab_set()

        container = tk.Frame(win, bg=COLORS["bg"])
        container.pack(fill="both", expand=True)

        def _on_done():
            if win.winfo_exists():
                win.destroy()
            self._load_invoices()

        InvoiceForm(container, on_done=_on_done)

    def _load_invoices(self):
        if not hasattr(self, "invoice_table"):
            return
        for item in self.invoice_table.get_children():
            self.invoice_table.delete(item)

        rows = list_invoices()
        for idx, row in enumerate(rows):
            _invoice_id, bill_no, str_no, ntn_no, to_text, invoice_date, order_date, total_qty, _created_at = row
            to_first_line = (to_text or "").splitlines()[0] if to_text else ""
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.invoice_table.insert(
                "",
                "end",
                values=(
                    bill_no or "",
                    str_no or "",
                    ntn_no or "",
                    to_first_line,
                    invoice_date or "",
                    order_date or "",
                    f"{float(total_qty or 0):,.2f}",
                ),
                tags=(tag,),
            )

    def _after_invoice(self):
        self.show_invoices_tab()

    def _update_sidebar_datetime(self):
        if not getattr(self, "datetime_label", None):
            return
        if not self.datetime_label.winfo_exists():
            return
        now_text = datetime.now().strftime("%d %b %Y  %I:%M:%S %p")
        self.datetime_label.config(text=now_text)
        self.root.after(1000, self._update_sidebar_datetime)
