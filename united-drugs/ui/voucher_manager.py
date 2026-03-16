import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from services.voucher_service import (
    list_vouchers,
    add_voucher,
    update_voucher,
    delete_voucher,
)
from ui.theme import COLORS, FONTS, SPACING, get_button_style, get_input_style, create_zebra_table


class VoucherManager(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.selected_id = None

        self.title("Add Voucher")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build()
        self._refresh()
        self._center()

    def _center(self):
        self.update_idletasks()
        w = 760
        h = 540
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
            text="Add Voucher",
            font=FONTS["section_header"],
            fg=COLORS["text_dark"],
            bg=COLORS["bg"]
        ).pack(side="left")

        form = tk.Frame(container, bg=COLORS["bg"])
        form.pack(fill="x", pady=(SPACING["lg"], 0))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=1)

        code_box = tk.Frame(form, bg=COLORS["bg"])
        code_box.grid(row=0, column=0, sticky="ew", padx=(0, SPACING["lg"]))
        tk.Label(code_box, text="Voucher Code", font=FONTS["label"], fg=COLORS["text_medium"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 6))
        self.code_entry = tk.Entry(code_box, **get_input_style())
        self.code_entry.pack(fill="x", ipady=8)

        percent_box = tk.Frame(form, bg=COLORS["bg"])
        percent_box.grid(row=0, column=1, sticky="ew", padx=(0, SPACING["lg"]))
        tk.Label(percent_box, text="Discount %", font=FONTS["label"], fg=COLORS["text_medium"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 6))
        self.percent_entry = tk.Entry(percent_box, **get_input_style())
        self.percent_entry.pack(fill="x", ipady=8)

        amount_box = tk.Frame(form, bg=COLORS["bg"])
        amount_box.grid(row=0, column=2, sticky="ew")
        tk.Label(amount_box, text="Discount Amount", font=FONTS["label"], fg=COLORS["text_medium"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 6))
        self.amount_entry = tk.Entry(amount_box, **get_input_style())
        self.amount_entry.pack(fill="x", ipady=8)

        tk.Label(
            container,
            text="Enter either percentage or amount.",
            font=FONTS["small"],
            fg=COLORS["text_medium"],
            bg=COLORS["bg"]
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

        actions = tk.Frame(container, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(SPACING["lg"], 0))
        tk.Button(actions, text="Add Voucher", command=self._add, **get_button_style("primary")).pack(side="left")
        tk.Button(actions, text="Update", command=self._update, **get_button_style("secondary")).pack(side="left", padx=(SPACING["sm"], 0))
        tk.Button(actions, text="Delete", command=self._delete, **get_button_style("secondary")).pack(side="left", padx=(SPACING["sm"], 0))
        tk.Button(actions, text="Close", command=self.destroy, **get_button_style("secondary")).pack(side="right")

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
            columns=("Code", "Type", "Value", "Created"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("Code", text="Voucher Code", anchor="w")
        self.tree.heading("Type", text="Type", anchor="w")
        self.tree.heading("Value", text="Value", anchor="e")
        self.tree.heading("Created", text="Created", anchor="w")
        self.tree.column("Code", width=240, anchor="w")
        self.tree.column("Type", width=120, anchor="w")
        self.tree.column("Value", width=120, anchor="e")
        self.tree.column("Created", width=200, anchor="w")

        create_zebra_table(self.tree)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        vouchers = list_vouchers()
        for idx, (voucher_id, code, discount_type, discount_value, created_at) in enumerate(vouchers):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            type_text = "Percent" if discount_type == "percent" else "Amount"
            value_text = f"{discount_value:,.2f}% " if discount_type == "percent" else f"{discount_value:,.2f}"
            self.tree.insert("", "end", iid=str(voucher_id), values=(code, type_text, value_text.strip(), created_at or ""), tags=(tag,))

        self.selected_id = None
        self.code_entry.delete(0, tk.END)
        self.percent_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)

    def _on_select(self, _):
        selection = self.tree.selection()
        if not selection:
            return

        self.selected_id = int(selection[0])
        values = self.tree.item(selection[0], "values")
        self.code_entry.delete(0, tk.END)
        self.code_entry.insert(0, values[0])
        self.percent_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)

        if values[1] == "Percent":
            self.percent_entry.insert(0, values[2].replace("%", "").replace(",", "").strip())
        else:
            self.amount_entry.insert(0, values[2].replace(",", "").strip())

    def _get_form_data(self):
        code = self.code_entry.get().strip().upper()
        percent_raw = self.percent_entry.get().strip()
        amount_raw = self.amount_entry.get().strip()

        if not code:
            raise ValueError("Please enter voucher code.")
        if not percent_raw and not amount_raw:
            raise ValueError("Please enter discount percentage or amount.")
        if percent_raw and amount_raw:
            raise ValueError("Please enter only one discount type.")

        if percent_raw:
            try:
                discount_value = float(percent_raw)
            except ValueError:
                raise ValueError("Discount percentage must be a number.")
            if discount_value <= 0 or discount_value > 100:
                raise ValueError("Discount percentage must be between 0 and 100.")
            discount_type = "percent"
        else:
            try:
                discount_value = float(amount_raw)
            except ValueError:
                raise ValueError("Discount amount must be a number.")
            if discount_value <= 0:
                raise ValueError("Discount amount must be greater than 0.")
            discount_type = "amount"

        return code, discount_type, discount_value

    def _add(self):
        try:
            code, discount_type, discount_value = self._get_form_data()
            add_voucher(code, discount_type, discount_value)
        except ValueError as exc:
            messagebox.showerror("Validation", str(exc))
            return
        except sqlite3.IntegrityError:
            messagebox.showerror("Validation", "Voucher code already exists.")
            return

        self._refresh()

    def _update(self):
        if not self.selected_id:
            messagebox.showerror("Validation", "Please select a voucher to update.")
            return

        try:
            code, discount_type, discount_value = self._get_form_data()
            update_voucher(self.selected_id, code, discount_type, discount_value)
        except ValueError as exc:
            messagebox.showerror("Validation", str(exc))
            return
        except sqlite3.IntegrityError:
            messagebox.showerror("Validation", "Voucher code already exists.")
            return

        self._refresh()

    def _delete(self):
        if not self.selected_id:
            messagebox.showerror("Validation", "Please select a voucher to delete.")
            return

        ok = messagebox.askyesno("Confirm", "Delete selected voucher?")
        if not ok:
            return

        delete_voucher(self.selected_id)
        self._refresh()
