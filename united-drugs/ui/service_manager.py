import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from services.service_service import (
    list_services,
    add_service,
    update_service,
    delete_service,
    get_service_usage_count,
)
from ui.theme import COLORS, FONTS, SPACING, get_button_style, get_input_style, create_zebra_table


class ServiceManager(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.selected_id = None

        self.title("Add Service")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build()
        self._refresh()
        self._center()

    def _center(self):
        self.update_idletasks()
        w = 720
        h = 520
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
            text="Add Service",
            font=FONTS["section_header"],
            fg=COLORS["text_dark"],
            bg=COLORS["bg"]
        ).pack(side="left")

        # Form
        form = tk.Frame(container, bg=COLORS["bg"])
        form.pack(fill="x", pady=(SPACING["lg"], 0))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        name_box = tk.Frame(form, bg=COLORS["bg"])
        name_box.grid(row=0, column=0, sticky="ew", padx=(0, SPACING["lg"]))
        tk.Label(name_box, text="Service Name", font=FONTS["label"], fg=COLORS["text_medium"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 6))
        self.name_entry = tk.Entry(name_box, **get_input_style())
        self.name_entry.pack(fill="x", ipady=8)

        price_box = tk.Frame(form, bg=COLORS["bg"])
        price_box.grid(row=0, column=1, sticky="ew")
        tk.Label(price_box, text="Price", font=FONTS["label"], fg=COLORS["text_medium"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 6))
        self.price_entry = tk.Entry(price_box, **get_input_style())
        self.price_entry.pack(fill="x", ipady=8)

        actions = tk.Frame(container, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(SPACING["lg"], 0))

        tk.Button(actions, text="Add Service", command=self._add, **get_button_style("primary")).pack(side="left")
        tk.Button(actions, text="Update", command=self._update, **get_button_style("secondary")).pack(side="left", padx=(SPACING["sm"], 0))
        tk.Button(actions, text="Delete", command=self._delete, **get_button_style("secondary")).pack(side="left", padx=(SPACING["sm"], 0))
        tk.Button(actions, text="Close", command=self.destroy, **get_button_style("secondary")).pack(side="right")

        body = tk.Frame(container, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, pady=(SPACING["lg"], 0))

        # Table
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
            columns=("Name", "Price", "Created"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("Name", text="Service Name", anchor="w")
        self.tree.heading("Price", text="Price", anchor="e")
        self.tree.heading("Created", text="Created", anchor="w")
        self.tree.column("Name", width=300, anchor="w")
        self.tree.column("Price", width=120, anchor="e")
        self.tree.column("Created", width=180, anchor="w")

        create_zebra_table(self.tree)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for idx, (service_id, name, price, created) in enumerate(list_services()):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", iid=str(service_id), values=(name, f"{price:,.2f}", created or ""), tags=(tag,))

        self.selected_id = None
        self.name_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)

    def _on_select(self, _):
        selection = self.tree.selection()
        if not selection:
            return
        self.selected_id = int(selection[0])
        values = self.tree.item(selection[0], "values")
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, values[0])
        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(0, values[1].replace(",", ""))

    def _add(self):
        name = self.name_entry.get().strip()
        price_raw = self.price_entry.get().strip()
        if not name or not price_raw:
            messagebox.showerror("Validation", "Please enter service name and price.")
            return
        try:
            price = float(price_raw)
        except ValueError:
            messagebox.showerror("Validation", "Price must be a number.")
            return

        try:
            add_service(name, price)
        except sqlite3.IntegrityError:
            messagebox.showerror("Validation", "Service name already exists.")
            return

        self._refresh()

    def _update(self):
        if not self.selected_id:
            messagebox.showerror("Validation", "Please select a service to update.")
            return
        name = self.name_entry.get().strip()
        price_raw = self.price_entry.get().strip()
        if not name or not price_raw:
            messagebox.showerror("Validation", "Please enter service name and price.")
            return
        try:
            price = float(price_raw)
        except ValueError:
            messagebox.showerror("Validation", "Price must be a number.")
            return

        try:
            update_service(self.selected_id, name, price)
        except sqlite3.IntegrityError:
            messagebox.showerror("Validation", "Service name already exists.")
            return

        self._refresh()

    def _delete(self):
        if not self.selected_id:
            messagebox.showerror("Validation", "Please select a service to delete.")
            return

        values = self.tree.item(str(self.selected_id), "values")
        name = values[0] if values else ""
        used_count = get_service_usage_count(name)

        if used_count > 0:
            ok = messagebox.askyesno(
                "Warning",
                f"This service is used in {used_count} invoice(s). Delete anyway?"
            )
            if not ok:
                return
        else:
            ok = messagebox.askyesno("Confirm", "Delete selected service?")
            if not ok:
                return

        delete_service(self.selected_id)
        self._refresh()
