import tkinter as tk
from tkinter import ttk
from services.service_service import list_services
from services.package_service import list_packages
from services.voucher_service import list_vouchers
from ui.service_manager import ServiceManager
from ui.package_manager import PackageManager
from ui.voucher_manager import VoucherManager
from ui.theme import COLORS, FONTS, SPACING, get_button_style, create_zebra_table


class CatalogManager(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.title("Catalog")
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self._build()
        self._refresh_all()
        self._center()

    def _center(self):
        self.update_idletasks()
        w = 980
        h = 640
        x = self.winfo_screenwidth() // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(900, 560)

    def _build(self):
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_columnconfigure(2, weight=1)

        header = tk.Frame(container, bg=COLORS["bg"])
        header.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, SPACING["lg"]))
        tk.Label(
            header,
            text="Catalog",
            font=FONTS["section_header"],
            fg=COLORS["text_dark"],
            bg=COLORS["bg"],
        ).pack(side="left")
        tk.Button(
            header,
            text="Refresh",
            command=self._refresh_all,
            **get_button_style("secondary"),
        ).pack(side="right")

        self.services_tree = self._build_section(
            container,
            column=0,
            title="Services",
            columns=("Name", "Price", "Created"),
            widths=(180, 90, 130),
            edit_text="Edit Selected",
            edit_command=self._edit_selected_service,
        )
        self.packages_tree = self._build_section(
            container,
            column=1,
            title="Packages",
            columns=("Name", "Price", "Created"),
            widths=(180, 90, 130),
            edit_text="Edit Selected",
            edit_command=self._edit_selected_package,
        )
        self.vouchers_tree = self._build_section(
            container,
            column=2,
            title="Vouchers",
            columns=("Code", "Type", "Value"),
            widths=(140, 90, 110),
            edit_text="Edit Selected",
            edit_command=self._edit_selected_voucher,
        )

        self.services_tree.bind("<Double-1>", lambda _e: self._edit_selected_service())
        self.packages_tree.bind("<Double-1>", lambda _e: self._edit_selected_package())
        self.vouchers_tree.bind("<Double-1>", lambda _e: self._edit_selected_voucher())

        actions = tk.Frame(container, bg=COLORS["bg"])
        actions.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(SPACING["lg"], 0))
        tk.Button(actions, text="Close", command=self.destroy, **get_button_style("secondary")).pack(side="right")

    def _build_section(
        self,
        parent,
        column,
        title,
        columns,
        widths,
        edit_text=None,
        edit_command=None,
    ):
        panel = tk.Frame(parent, bg=COLORS["border"])
        panel.grid(row=1, column=column, sticky="nsew", padx=(0 if column == 0 else SPACING["md"], 0))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        card = tk.Frame(panel, bg=COLORS["card"])
        card.pack(fill="both", expand=True, padx=1, pady=1)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        top = tk.Frame(card, bg=COLORS["card"])
        top.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])
        tk.Label(top, text=title, font=FONTS["label"], fg=COLORS["text_dark"], bg=COLORS["card"]).pack(side="left")
        if edit_text and edit_command:
            tk.Button(top, text=edit_text, command=edit_command, **get_button_style("secondary")).pack(
                side="right", padx=(SPACING["sm"], 0)
            )

        table_frame = tk.Frame(card, bg=COLORS["card"])
        table_frame.grid(row=1, column=0, sticky="nsew", padx=SPACING["md"], pady=(0, SPACING["md"]))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")

        tree = ttk.Treeview(table_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=tree.yview)

        for idx, col in enumerate(columns):
            anchor = "e" if col in ("Price", "Value") else "w"
            tree.heading(col, text=col, anchor=anchor)
            tree.column(col, width=widths[idx], anchor=anchor, minwidth=80)

        create_zebra_table(tree)
        return tree

    def _refresh_all(self):
        self._fill_services()
        self._fill_packages()
        self._fill_vouchers()

    def _fill_services(self):
        for item in self.services_tree.get_children():
            self.services_tree.delete(item)
        for idx, (service_id, name, price, created_at) in enumerate(list_services()):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.services_tree.insert(
                "",
                "end",
                iid=f"s-{service_id}",
                values=(name, f"{price:,.2f}", created_at or ""),
                tags=(tag,),
            )

    def _fill_packages(self):
        for item in self.packages_tree.get_children():
            self.packages_tree.delete(item)
        for idx, (package_id, name, created_at, price) in enumerate(list_packages()):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.packages_tree.insert(
                "",
                "end",
                iid=f"p-{package_id}",
                values=(name, f"{price:,.2f}", created_at or ""),
                tags=(tag,),
            )

    def _fill_vouchers(self):
        for item in self.vouchers_tree.get_children():
            self.vouchers_tree.delete(item)
        for idx, (voucher_id, code, discount_type, discount_value, _) in enumerate(list_vouchers()):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            type_text = "Percent" if discount_type == "percent" else "Amount"
            value_text = f"{discount_value:,.2f}% " if discount_type == "percent" else f"{discount_value:,.2f}"
            self.vouchers_tree.insert(
                "",
                "end",
                iid=f"v-{voucher_id}",
                values=(code, type_text, value_text.strip()),
                tags=(tag,),
            )

    def _edit_selected_service(self):
        selection = self.services_tree.selection()
        editor = ServiceManager(self)
        if selection:
            service_id = selection[0].replace("s-", "")
            if editor.tree.exists(service_id):
                editor.tree.selection_set(service_id)
                editor.tree.focus(service_id)
                editor.tree.event_generate("<<TreeviewSelect>>")
        self.wait_window(editor)
        self._refresh_all()

    def _edit_selected_package(self):
        selection = self.packages_tree.selection()
        editor = PackageManager(self)
        if selection:
            package_id = selection[0].replace("p-", "")
            if editor.tree.exists(package_id):
                editor.tree.selection_set(package_id)
                editor.tree.focus(package_id)
                editor.tree.event_generate("<<TreeviewSelect>>")
        self.wait_window(editor)
        self._refresh_all()

    def _edit_selected_voucher(self):
        selection = self.vouchers_tree.selection()
        editor = VoucherManager(self)
        if selection:
            voucher_id = selection[0].replace("v-", "")
            if editor.tree.exists(voucher_id):
                editor.tree.selection_set(voucher_id)
                editor.tree.focus(voucher_id)
                editor.tree.event_generate("<<TreeviewSelect>>")
        self.wait_window(editor)
        self._refresh_all()
