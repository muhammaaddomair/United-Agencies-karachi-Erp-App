import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from services.inventory_service import list_inventory_items
from services.invoice_service import save_invoice
from ui.date_picker import DatePicker
from ui.theme import COLORS, FONTS, SPACING, create_zebra_table, get_button_style, get_input_style


class ProductSelectorWindow(tk.Toplevel):
    def __init__(self, parent, on_add):
        super().__init__(parent)
        self.on_add = on_add
        self.title("Select Product")
        self.configure(bg=COLORS["bg"])
        self.transient(parent)
        self.grab_set()
        self.geometry("880x520")
        self.minsize(760, 420)

        self.qty_var = tk.StringVar()
        self.rows_by_id = {}

        self._build()
        self._load_products()

    def _build(self):
        root = tk.Frame(self, bg=COLORS["bg"])
        root.pack(fill="both", expand=True, padx=SPACING["lg"], pady=SPACING["lg"])
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        tk.Label(root, text="Select Product from Inventory", font=FONTS["section_header"], bg=COLORS["bg"], fg=COLORS["text_dark"]).grid(
            row=0, column=0, sticky="w", pady=(0, SPACING["md"])
        )

        table_wrap = tk.Frame(root, bg=COLORS["card"])
        table_wrap.grid(row=1, column=0, sticky="nsew")
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")

        cols = ("Reg No", "Batch No", "Product", "Available Qty")
        self.table = ttk.Treeview(table_wrap, columns=cols, show="headings", yscrollcommand=scrollbar.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.table.yview)

        widths = {"Reg No": 120, "Batch No": 120, "Product": 420, "Available Qty": 120}
        for col in cols:
            anchor = "e" if col == "Available Qty" else "w"
            self.table.heading(col, text=col, anchor=anchor)
            self.table.column(col, width=widths[col], anchor=anchor, minwidth=80)
        create_zebra_table(self.table)

        actions = tk.Frame(root, bg=COLORS["bg"])
        actions.grid(row=2, column=0, sticky="ew", pady=(SPACING["md"], 0))
        tk.Label(actions, text="Quantity", font=FONTS["label"], bg=COLORS["bg"], fg=COLORS["text_medium"]).pack(side="left")
        tk.Entry(actions, textvariable=self.qty_var, width=12, **get_input_style()).pack(side="left", padx=(SPACING["sm"], SPACING["md"]), ipady=4)
        tk.Button(actions, text="Add Product", command=self._add_selected, **get_button_style("primary")).pack(side="left")
        tk.Button(actions, text="Cancel", command=self.destroy, **get_button_style("secondary")).pack(side="right")

    def _load_products(self):
        for item in self.table.get_children():
            self.table.delete(item)
        self.rows_by_id = {}

        rows = list_inventory_items()
        visible_idx = 0
        for row in rows:
            item_id, reg_no, batch_no, _mfg, _exp, qty, desc, trade_price, discount_percent, _created = row
            available = float(qty or 0)
            if available <= 0:
                continue
            unit_price = float(trade_price or 0) * (1 - float(discount_percent or 0) / 100.0)
            self.rows_by_id[item_id] = {
                "inventory_item_id": item_id,
                "reg_no": reg_no or "",
                "batch_no": batch_no or "",
                "product_description": desc or "",
                "available_qty": available,
                "unit_price": max(0.0, unit_price),
            }
            tag = "evenrow" if visible_idx % 2 == 0 else "oddrow"
            self.table.insert(
                "",
                "end",
                iid=str(item_id),
                values=(reg_no or "", batch_no or "", desc or "", f"{available:,.2f}"),
                tags=(tag,),
            )
            visible_idx += 1

    def _add_selected(self):
        sel = self.table.selection()
        if not sel:
            messagebox.showerror("Selection Required", "Please select a product.")
            return
        try:
            qty = float((self.qty_var.get() or "").strip())
        except Exception:
            messagebox.showerror("Validation", "Quantity must be numeric.")
            return
        if qty <= 0:
            messagebox.showerror("Validation", "Quantity must be greater than 0.")
            return

        item_id = int(sel[0])
        row = self.rows_by_id.get(item_id)
        if not row:
            messagebox.showerror("Error", "Selected product could not be loaded.")
            return
        if qty > row["available_qty"]:
            messagebox.showerror("Validation", f"Only {row['available_qty']:,.2f} available in inventory.")
            return

        self.on_add({**row, "selected_qty": qty})
        self.destroy()


class InvoiceForm:
    def __init__(self, parent, on_done):
        self.parent = parent
        self.on_done = on_done
        self.bill_year_suffix = f"/{datetime.now().year}"
        self.selected_products = {}
        self._build()

    def _build(self):
        root = tk.Frame(self.parent, bg=COLORS["bg"])
        root.pack(fill="both", expand=True)

        card_outer = tk.Frame(root, bg=COLORS["border"])
        card_outer.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        card = tk.Frame(card_outer, bg=COLORS["card"])
        card.pack(fill="both", expand=True, padx=1, pady=1)
        card.grid_rowconfigure(2, weight=1)
        card.grid_columnconfigure(0, weight=1)

        header = tk.Frame(card, bg=COLORS["card"])
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["xl"], pady=(SPACING["lg"], SPACING["md"]))
        tk.Label(header, text="Create Invoice", font=FONTS["section_header"], bg=COLORS["card"], fg=COLORS["text_dark"]).pack(side="left")
        tk.Button(
            header,
            text="Add Product",
            command=self._open_product_selector,
            **get_button_style("primary"),
        ).pack(side="right")

        form = tk.Frame(card, bg=COLORS["card"])
        form.grid(row=1, column=0, sticky="ew", padx=SPACING["xl"])
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        digits_cmd = (form.register(self._validate_digits), "%P")
        bill_prefix_cmd = (form.register(self._validate_bill_prefix), "%P")

        self.str_no_var = tk.StringVar()
        self.ntn_no_var = tk.StringVar()
        self.bill_prefix_var = tk.StringVar()
        self.delivery_challan_var = tk.StringVar()
        self.order_contract_var = tk.StringVar()
        self.order_date_var = tk.StringVar()
        self.inspection_note_var = tk.StringVar()
        self.invoice_date_var = tk.StringVar()

        self._entry_field(form, 0, 0, "STR No", self.str_no_var, validate="key", validatecommand=digits_cmd)
        self._entry_field(form, 0, 1, "NTN Number", self.ntn_no_var, validate="key", validatecommand=digits_cmd)
        self._bill_no_field(form, 1, 0, "Bill No", self.bill_prefix_var, validate="key", validatecommand=bill_prefix_cmd)
        self._entry_field(form, 1, 1, "Delivery Challan No", self.delivery_challan_var)
        self._entry_field(form, 2, 0, "Your Order/Contract Number", self.order_contract_var)
        self._date_field(form, 2, 1, "Your Order Date", self.order_date_var)
        self._entry_field(form, 3, 0, "Inspection Note No", self.inspection_note_var)
        self._date_field(form, 3, 1, "Invoice Date", self.invoice_date_var)
        self._to_field(form, 4, 0, "To", col_span=2)

        product_card = tk.Frame(card, bg=COLORS["card"])
        product_card.grid(row=2, column=0, sticky="nsew", padx=SPACING["xl"], pady=(SPACING["lg"], SPACING["md"]))
        product_card.grid_rowconfigure(1, weight=1)
        product_card.grid_columnconfigure(0, weight=1)

        top = tk.Frame(product_card, bg=COLORS["card"])
        top.grid(row=0, column=0, sticky="ew", pady=(0, SPACING["sm"]))
        tk.Label(top, text="Selected Products", font=FONTS["label"], bg=COLORS["card"], fg=COLORS["text_medium"]).pack(side="left")
        tk.Button(top, text="Add Product", command=self._open_product_selector, **get_button_style("secondary")).pack(side="right")
        tk.Button(top, text="Remove Selected", command=self._remove_selected_product, **get_button_style("secondary")).pack(
            side="right", padx=(0, SPACING["sm"])
        )

        table_wrap = tk.Frame(product_card, bg=COLORS["card"])
        table_wrap.grid(row=1, column=0, sticky="nsew")
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")
        cols = ("Reg No", "Batch No", "Product", "Available", "Selected Qty")
        self.product_table = ttk.Treeview(table_wrap, columns=cols, show="headings", yscrollcommand=scrollbar.set)
        self.product_table.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.product_table.yview)
        widths = {"Reg No": 100, "Batch No": 100, "Product": 380, "Available": 100, "Selected Qty": 110}
        for col in cols:
            anchor = "e" if col in ("Available", "Selected Qty") else "w"
            self.product_table.heading(col, text=col, anchor=anchor)
            self.product_table.column(col, width=widths[col], minwidth=80, anchor=anchor)
        create_zebra_table(self.product_table)

        actions = tk.Frame(card, bg=COLORS["card"])
        actions.grid(row=3, column=0, sticky="ew", padx=SPACING["xl"], pady=(0, SPACING["xl"]))
        tk.Button(actions, text="Cancel", command=self.on_done, **get_button_style("secondary")).pack(side="right")
        tk.Button(actions, text="Save Invoice", command=self._save, **get_button_style("primary")).pack(
            side="right", padx=(0, SPACING["sm"])
        )

    def _entry_field(self, parent, row, col, label, variable, validate=None, validatecommand=None):
        frame = tk.Frame(parent, bg=COLORS["card"])
        frame.grid(row=row, column=col, sticky="ew", padx=(0 if col == 0 else SPACING["lg"], 0), pady=(0, SPACING["lg"]))
        tk.Label(frame, text=label, font=FONTS["label"], bg=COLORS["card"], fg=COLORS["text_medium"]).pack(anchor="w", pady=(0, SPACING["xs"]))
        kwargs = get_input_style()
        if validate:
            kwargs["validate"] = validate
        if validatecommand:
            kwargs["validatecommand"] = validatecommand
        tk.Entry(frame, textvariable=variable, **kwargs).pack(fill="x", ipady=8)

    def _bill_no_field(self, parent, row, col, label, variable, validate=None, validatecommand=None):
        frame = tk.Frame(parent, bg=COLORS["card"])
        frame.grid(row=row, column=col, sticky="ew", padx=(0 if col == 0 else SPACING["lg"], 0), pady=(0, SPACING["lg"]))
        tk.Label(frame, text=label, font=FONTS["label"], bg=COLORS["card"], fg=COLORS["text_medium"]).pack(anchor="w", pady=(0, SPACING["xs"]))
        row_wrap = tk.Frame(frame, bg=COLORS["card"])
        row_wrap.pack(fill="x")
        kwargs = get_input_style()
        if validate:
            kwargs["validate"] = validate
        if validatecommand:
            kwargs["validatecommand"] = validatecommand
        tk.Entry(row_wrap, textvariable=variable, **kwargs).pack(side="left", fill="x", expand=True, ipady=8)
        tk.Label(row_wrap, text=self.bill_year_suffix, font=FONTS["body"], bg=COLORS["card"], fg=COLORS["text_medium"]).pack(
            side="left", padx=(SPACING["sm"], 0)
        )

    def _date_field(self, parent, row, col, label, variable):
        frame = tk.Frame(parent, bg=COLORS["card"])
        frame.grid(row=row, column=col, sticky="ew", padx=(0 if col == 0 else SPACING["lg"], 0), pady=(0, SPACING["lg"]))
        tk.Label(frame, text=label, font=FONTS["label"], bg=COLORS["card"], fg=COLORS["text_medium"]).pack(anchor="w", pady=(0, SPACING["xs"]))
        row_wrap = tk.Frame(frame, bg=COLORS["card"])
        row_wrap.pack(fill="x")
        entry = tk.Entry(row_wrap, textvariable=variable, state="readonly", **get_input_style())
        entry.pack(side="left", fill="x", expand=True, ipady=8)
        tk.Button(
            row_wrap,
            text="Pick",
            command=lambda e=entry: self._open_date_picker(variable, e),
            **get_button_style("secondary"),
        ).pack(
            side="left", padx=(SPACING["xs"], 0), ipady=4
        )

    def _to_field(self, parent, row, col, label, col_span=1):
        frame = tk.Frame(parent, bg=COLORS["card"])
        frame.grid(
            row=row,
            column=col,
            columnspan=col_span,
            sticky="ew",
            padx=(0 if col == 0 else SPACING["lg"], 0),
            pady=(0, SPACING["lg"]),
        )
        tk.Label(frame, text=label, font=FONTS["label"], bg=COLORS["card"], fg=COLORS["text_medium"]).pack(anchor="w", pady=(0, SPACING["xs"]))
        text_wrap = tk.Frame(frame, bg=COLORS["card"])
        text_wrap.pack(fill="x")
        self.to_text = tk.Text(
            text_wrap,
            height=3,
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text_dark"],
            relief="solid",
            borderwidth=1,
            insertbackground=COLORS["primary"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["primary"],
            wrap="word",
        )
        self.to_text.pack(side="left", fill="x", expand=True)
        scrollbar = tk.Scrollbar(text_wrap, orient="vertical", command=self.to_text.yview)
        scrollbar.pack(side="left", fill="y")
        self.to_text.configure(yscrollcommand=scrollbar.set)

    def _open_date_picker(self, target_var, anchor_widget):
        initial = None
        value = (target_var.get() or "").strip()
        if value:
            try:
                initial = datetime.strptime(value, "%Y-%m-%d").date()
            except Exception:
                initial = None
        DatePicker(
            self.parent.winfo_toplevel(),
            lambda selected: target_var.set(selected),
            initial_date=initial,
            anchor_widget=anchor_widget,
        )

    def _validate_digits(self, value):
        return value == "" or value.isdigit()

    def _validate_bill_prefix(self, value):
        return re.fullmatch(r"[A-Za-z0-9-]*", value or "") is not None

    def _open_product_selector(self):
        ProductSelectorWindow(self.parent.winfo_toplevel(), self._add_product)

    def _add_product(self, product):
        item_id = int(product["inventory_item_id"])
        prev = self.selected_products.get(item_id)
        if prev:
            total = float(prev["selected_qty"]) + float(product["selected_qty"])
            if total > float(product["available_qty"]):
                messagebox.showerror(
                    "Validation",
                    f"Selected quantity exceeds available stock ({product['available_qty']:,.2f}).",
                )
                return
            prev["selected_qty"] = total
            self.selected_products[item_id] = prev
        else:
            self.selected_products[item_id] = product
        self._refresh_selected_products()

    def _remove_selected_product(self):
        sel = self.product_table.selection()
        if not sel:
            return
        item_id = int(sel[0])
        if item_id in self.selected_products:
            del self.selected_products[item_id]
        self._refresh_selected_products()

    def _refresh_selected_products(self):
        for item in self.product_table.get_children():
            self.product_table.delete(item)
        idx = 0
        for item_id, p in self.selected_products.items():
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.product_table.insert(
                "",
                "end",
                iid=str(item_id),
                values=(
                    p.get("reg_no", ""),
                    p.get("batch_no", ""),
                    p.get("product_description", ""),
                    f"{float(p.get('available_qty', 0)):,.2f}",
                    f"{float(p.get('selected_qty', 0)):,.2f}",
                ),
                tags=(tag,),
            )
            idx += 1

    def _save(self):
        str_no = (self.str_no_var.get() or "").strip()
        ntn_no = (self.ntn_no_var.get() or "").strip()
        bill_prefix = (self.bill_prefix_var.get() or "").strip()
        bill_no = f"{bill_prefix}{self.bill_year_suffix}" if bill_prefix else ""
        delivery_challan_no = (self.delivery_challan_var.get() or "").strip()
        order_contract_no = (self.order_contract_var.get() or "").strip()
        order_date = (self.order_date_var.get() or "").strip()
        inspection_note_no = (self.inspection_note_var.get() or "").strip()
        invoice_date = (self.invoice_date_var.get() or "").strip()
        to_text = self.to_text.get("1.0", "end").strip()

        if not str_no or not ntn_no or not bill_no or not invoice_date or not to_text:
            messagebox.showerror("Validation", "Please fill required fields: STR No, NTN Number, Bill No, Invoice Date, To.")
            return
        if not self._validate_digits(str_no) or not self._validate_digits(ntn_no):
            messagebox.showerror("Validation", "STR No and NTN Number must contain numbers only.")
            return
        if not bill_prefix or not self._validate_bill_prefix(bill_prefix):
            messagebox.showerror("Validation", "Bill No prefix allows only letters, numbers, and hyphen.")
            return
        if not self.selected_products:
            messagebox.showerror("Validation", "Please select at least one product.")
            return

        products = []
        for product in self.selected_products.values():
            products.append(
                {
                    "inventory_item_id": int(product["inventory_item_id"]),
                    "product_description": product["product_description"],
                    "quantity": float(product["selected_qty"]),
                    "unit_price": float(product.get("unit_price", 0.0)),
                }
            )

        data = {
            "str_no": str_no,
            "ntn_no": ntn_no,
            "bill_no": bill_no,
            "delivery_challan_no": delivery_challan_no,
            "order_contract_no": order_contract_no,
            "order_date": order_date,
            "inspection_note_no": inspection_note_no,
            "invoice_date": invoice_date,
            "to_text": to_text,
        }

        try:
            save_invoice(data, products)
        except Exception as exc:
            messagebox.showerror("Save Failed", str(exc))
            return

        messagebox.showinfo("Success", "Invoice saved and inventory updated successfully.")
        self.on_done()
