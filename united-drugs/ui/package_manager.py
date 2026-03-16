import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from services.package_service import (
    list_packages,
    add_package,
    update_package,
    delete_package,
    get_package_items,
    get_package_usage_count,
)
from ui.service_picker import ServicePicker
from ui.theme import COLORS, FONTS, SPACING, get_button_style, get_input_style, create_zebra_table


class PackageManager(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.selected_id = None
        self.selected_services = []

        self.title("Add Package")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build()
        self._refresh_packages()
        self._center()

    def _center(self):
        self.update_idletasks()
        w = 780
        h = 620
        x = self.winfo_screenwidth() // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        header = tk.Frame(container, bg=COLORS["bg"])
        header.pack(fill="x")
        tk.Label(
            header,
            text="Add Package",
            font=FONTS["section_header"],
            fg=COLORS["text_dark"],
            bg=COLORS["bg"]
        ).pack(side="left")

        # Package name
        name_box = tk.Frame(container, bg=COLORS["bg"])
        name_box.pack(fill="x", pady=(SPACING["lg"], 0))
        tk.Label(
            name_box,
            text="Package Name",
            font=FONTS["label"],
            fg=COLORS["text_medium"],
            bg=COLORS["bg"]
        ).pack(anchor="w", pady=(0, 6))
        self.name_entry = tk.Entry(name_box, **get_input_style())
        self.name_entry.pack(fill="x", ipady=8)

        # Package price (independent from service prices)
        price_box = tk.Frame(container, bg=COLORS["bg"])
        price_box.pack(fill="x", pady=(SPACING["sm"], 0))
        tk.Label(
            price_box,
            text="Package Price",
            font=FONTS["label"],
            fg=COLORS["text_medium"],
            bg=COLORS["bg"]
        ).pack(anchor="w", pady=(0, 6))
        self.package_price_entry = tk.Entry(price_box, **get_input_style())
        self.package_price_entry.pack(fill="x", ipady=8)

        # Service adder
        service_row = tk.Frame(container, bg=COLORS["bg"])
        service_row.pack(fill="x", pady=(SPACING["lg"], 0))
        service_row.grid_columnconfigure(0, weight=1)

        service_box = tk.Frame(service_row, bg=COLORS["bg"])
        service_box.grid(row=0, column=0, sticky="ew")
        service_box.grid_columnconfigure(0, weight=1)

        name_col = tk.Frame(service_box, bg=COLORS["bg"])
        name_col.grid(row=0, column=0, sticky="ew", padx=(0, SPACING["lg"]))
        tk.Label(name_col, text="Service Name", font=FONTS["label"], fg=COLORS["text_medium"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 6))
        self.service_name_entry = tk.Entry(name_col, **get_input_style())
        self.service_name_entry.pack(fill="x", ipady=6)

        service_actions = tk.Frame(container, bg=COLORS["bg"])
        service_actions.pack(fill="x", pady=(SPACING["sm"], 0))
        tk.Button(
            service_actions,
            text="Add Service",
            command=self._add_service_manual,
            **get_button_style("secondary")
        ).pack(side="left")
        tk.Button(
            service_actions,
            text="Select From Services",
            command=self._open_service_picker,
            **get_button_style("secondary")
        ).pack(side="left", padx=(SPACING["sm"], 0))
        tk.Button(
            service_actions,
            text="Remove Selected",
            command=self._remove_selected_service,
            **get_button_style("secondary")
        ).pack(side="left", padx=(SPACING["sm"], 0))

        # Selected services list
        list_box = tk.Frame(container, bg=COLORS["bg"])
        list_box.pack(fill="x", pady=(SPACING["sm"], 0))
        tk.Label(
            list_box,
            text="Services in Package",
            font=FONTS["label"],
            fg=COLORS["text_medium"],
            bg=COLORS["bg"]
        ).pack(anchor="w", pady=(0, 6))
        self.service_list = tk.Listbox(
            list_box,
            height=4,
            font=FONTS["body"],
            bd=1,
            relief="solid"
        )
        self.service_list.pack(fill="x")

        # Package actions
        actions = tk.Frame(container, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(SPACING["lg"], 0))
        tk.Button(actions, text="Add Package", command=self._add_package, **get_button_style("primary")).pack(side="left")
        tk.Button(actions, text="Update", command=self._update_package, **get_button_style("secondary")).pack(side="left", padx=(SPACING["sm"], 0))
        tk.Button(actions, text="Delete", command=self._delete_package, **get_button_style("secondary")).pack(side="left", padx=(SPACING["sm"], 0))
        tk.Button(actions, text="Close", command=self.destroy, **get_button_style("secondary")).pack(side="right")

        # Table
        body = tk.Frame(container, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, pady=(SPACING["lg"], 0))

        table_outer = tk.Frame(body, bg=COLORS["border"])
        table_outer.pack(fill="both", expand=True)
        table = tk.Frame(table_outer, bg=COLORS["card"])
        table.pack(fill="both", expand=True, padx=1, pady=1)
        table.grid_rowconfigure(0, weight=1)
        table.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(table, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree = ttk.Treeview(
            table,
            columns=("Name", "Total", "Created"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("Name", text="Package Name", anchor="w")
        self.tree.heading("Total", text="Price", anchor="e")
        self.tree.heading("Created", text="Created", anchor="w")
        self.tree.column("Name", width=320, anchor="w")
        self.tree.column("Total", width=120, anchor="e")
        self.tree.column("Created", width=180, anchor="w")

        create_zebra_table(self.tree)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _refresh_packages(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for idx, (package_id, name, created, total) in enumerate(list_packages()):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", iid=str(package_id), values=(name, f"{total:,.2f}", created or ""), tags=(tag,))

        self.selected_id = None
        self.name_entry.delete(0, tk.END)
        self.package_price_entry.delete(0, tk.END)
        self.service_name_entry.delete(0, tk.END)
        self.selected_services = []
        self._refresh_service_list()

    def _refresh_service_list(self):
        self.service_list.delete(0, tk.END)
        for name in self.selected_services:
            self.service_list.insert(tk.END, name)

    def _add_service_manual(self):
        name = self.service_name_entry.get().strip()
        if not name:
            messagebox.showerror("Validation", "Please enter service name.")
            return

        self.selected_services.append(name)
        self.service_name_entry.delete(0, tk.END)
        self._refresh_service_list()

    def _open_service_picker(self):
        ServicePicker(self.parent.winfo_toplevel(), self._add_service_from_picker)

    def _add_service_from_picker(self, name, _price):
        self.selected_services.append(name)
        self._refresh_service_list()

    def _remove_selected_service(self):
        selection = list(self.service_list.curselection())
        if not selection:
            return
        for idx in reversed(selection):
            if 0 <= idx < len(self.selected_services):
                self.selected_services.pop(idx)
        self._refresh_service_list()

    def _on_select(self, _):
        selection = self.tree.selection()
        if not selection:
            return
        self.selected_id = int(selection[0])
        values = self.tree.item(selection[0], "values")
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, values[0])
        self.package_price_entry.delete(0, tk.END)
        self.package_price_entry.insert(0, values[1].replace(",", ""))

        items = get_package_items(self.selected_id)
        self.selected_services = [name for _, name in items]
        self._refresh_service_list()

    def _add_package(self):
        name = self.name_entry.get().strip()
        package_price_raw = self.package_price_entry.get().strip()
        if not name or not self.selected_services:
            messagebox.showerror("Validation", "Please enter package name and add at least one service.")
            return

        try:
            package_price = float(package_price_raw)
        except ValueError:
            messagebox.showerror("Validation", "Package price must be a number.")
            return

        try:
            add_package(name, package_price, self.selected_services)
        except sqlite3.IntegrityError:
            messagebox.showerror("Validation", "Package name already exists.")
            return

        self._refresh_packages()

    def _update_package(self):
        if not self.selected_id:
            messagebox.showerror("Validation", "Please select a package to update.")
            return
        name = self.name_entry.get().strip()
        package_price_raw = self.package_price_entry.get().strip()
        if not name or not self.selected_services:
            messagebox.showerror("Validation", "Please enter package name and add at least one service.")
            return

        try:
            package_price = float(package_price_raw)
        except ValueError:
            messagebox.showerror("Validation", "Package price must be a number.")
            return

        try:
            update_package(self.selected_id, name, package_price, self.selected_services)
        except sqlite3.IntegrityError:
            messagebox.showerror("Validation", "Package name already exists.")
            return

        self._refresh_packages()

    def _delete_package(self):
        if not self.selected_id:
            messagebox.showerror("Validation", "Please select a package to delete.")
            return

        values = self.tree.item(str(self.selected_id), "values")
        name = values[0] if values else ""
        used_count = get_package_usage_count(name)

        if used_count > 0:
            ok = messagebox.askyesno(
                "Warning",
                f"This package is used in {used_count} invoice(s). Delete anyway?"
            )
            if not ok:
                return
        else:
            ok = messagebox.askyesno("Confirm", "Delete selected package?")
            if not ok:
                return

        delete_package(self.selected_id)
        self._refresh_packages()
