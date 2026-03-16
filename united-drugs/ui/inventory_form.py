import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

from services.inventory_service import list_inventory_items, save_inventory_item, update_inventory_item
from ui.date_picker import DatePicker
from ui.theme import (
    COLORS,
    FONTS,
    SPACING,
    create_zebra_table,
    get_button_style,
    get_input_style,
)


class AddProductWindow(tk.Toplevel):
    def __init__(self, parent, on_saved, item_id=None, initial_data=None):
        super().__init__(parent)
        self.on_saved = on_saved
        self.item_id = item_id
        self.initial_data = initial_data or {}
        self.is_edit = item_id is not None
        self.title("Edit Product" if self.is_edit else "Add Product")
        self.configure(bg=COLORS["bg"])
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)

        self.reg_no_var = tk.StringVar()
        self.batch_no_var = tk.StringVar()
        self.mfg_date_var = tk.StringVar()
        self.exp_date_var = tk.StringVar()
        self.quantity_var = tk.StringVar()
        self.product_description_var = tk.StringVar()
        self.trade_price_var = tk.StringVar()
        self.discount_percent_var = tk.StringVar()

        self._build()
        self._prefill()
        self._center()

    def _center(self):
        self.update_idletasks()
        w = 920
        h = 680
        x = self.winfo_screenwidth() // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(760, 520)

    def _build(self):
        shell = tk.Frame(self, bg=COLORS["bg"])
        shell.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        card_outer = tk.Frame(shell, bg=COLORS["border"])
        card_outer.grid(row=0, column=0, sticky="nsew")
        card_outer.grid_rowconfigure(0, weight=1)
        card_outer.grid_columnconfigure(0, weight=1)

        card = tk.Frame(card_outer, bg=COLORS["card"])
        card.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(card, bg=COLORS["card"], highlightthickness=0)
        vscroll = tk.Scrollbar(card, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")

        content = tk.Frame(canvas, bg=COLORS["card"])
        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_content_configure(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        content.bind("<Configure>", _on_content_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.bind("<Destroy>", lambda _e: canvas.unbind_all("<MouseWheel>"))

        head = tk.Frame(content, bg=COLORS["card"])
        head.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["lg"], SPACING["md"]))
        tk.Label(
            head,
            text="Edit Product" if self.is_edit else "Create Product",
            font=FONTS["section_header"],
            bg=COLORS["card"],
            fg=COLORS["text_dark"],
        ).pack(side="left")

        form = tk.Frame(content, bg=COLORS["card"])
        form.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(0, SPACING["md"]))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        self._entry_field(form, 0, 0, "Reg No", self.reg_no_var)
        self._entry_field(form, 0, 1, "Batch No", self.batch_no_var)
        self._date_field(form, 1, 0, "Mfg Date", self.mfg_date_var)
        self._date_field(form, 1, 1, "Exp Date", self.exp_date_var)
        self._entry_field(form, 2, 0, "Quantity", self.quantity_var)
        self._entry_field(form, 2, 1, "Product Description", self.product_description_var)
        self._entry_field(form, 3, 0, "Trading Price", self.trade_price_var)
        self._entry_field(form, 3, 1, "Discount (%)", self.discount_percent_var)

        actions = tk.Frame(content, bg=COLORS["card"])
        actions.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["md"], SPACING["xl"]))
        tk.Button(actions, text="Cancel", command=self.destroy, **get_button_style("secondary")).pack(side="right")
        tk.Button(
            actions,
            text="Update Product" if self.is_edit else "Save Product",
            command=self._save,
            **get_button_style("primary"),
        ).pack(
            side="right", padx=(0, SPACING["sm"])
        )

    def _prefill(self):
        if not self.is_edit:
            return
        self.reg_no_var.set(self.initial_data.get("reg_no", ""))
        self.batch_no_var.set(self.initial_data.get("batch_no", ""))
        self.mfg_date_var.set(self.initial_data.get("mfg_date", ""))
        self.exp_date_var.set(self.initial_data.get("exp_date", ""))
        self.quantity_var.set(str(self.initial_data.get("quantity", "")))
        self.product_description_var.set(self.initial_data.get("product_description", ""))
        self.trade_price_var.set(str(self.initial_data.get("trade_price", "")))
        self.discount_percent_var.set(str(self.initial_data.get("discount_percent", "")))

    def _entry_field(self, parent, row, col, label, variable):
        frame = tk.Frame(parent, bg=COLORS["card"])
        frame.grid(
            row=row,
            column=col,
            sticky="ew",
            padx=(0 if col == 0 else SPACING["lg"], 0),
            pady=(0, SPACING["lg"]),
        )
        tk.Label(frame, text=label, font=FONTS["label"], bg=COLORS["card"], fg=COLORS["text_medium"]).pack(
            anchor="w", pady=(0, SPACING["xs"])
        )
        tk.Entry(frame, textvariable=variable, **get_input_style()).pack(fill="x", ipady=8)

    def _date_field(self, parent, row, col, label, variable):
        frame = tk.Frame(parent, bg=COLORS["card"])
        frame.grid(
            row=row,
            column=col,
            sticky="ew",
            padx=(0 if col == 0 else SPACING["lg"], 0),
            pady=(0, SPACING["lg"]),
        )
        tk.Label(frame, text=label, font=FONTS["label"], bg=COLORS["card"], fg=COLORS["text_medium"]).pack(
            anchor="w", pady=(0, SPACING["xs"])
        )
        row_wrap = tk.Frame(frame, bg=COLORS["card"])
        row_wrap.pack(fill="x")
        entry = tk.Entry(row_wrap, textvariable=variable, state="readonly", **get_input_style())
        entry.pack(
            side="left", fill="x", expand=True, ipady=8
        )
        tk.Button(
            row_wrap,
            text="Pick",
            command=lambda e=entry: self._open_date_picker(variable, e),
            **get_button_style("secondary"),
        ).pack(side="left", padx=(SPACING["xs"], 0), ipady=4)

    def _open_date_picker(self, target_var, anchor_widget):
        initial = None
        value = (target_var.get() or "").strip()
        if value:
            try:
                initial = datetime.strptime(value, "%Y-%m-%d").date()
            except Exception:
                initial = None
        DatePicker(self, lambda selected: target_var.set(selected), initial_date=initial, anchor_widget=anchor_widget)

    def _to_float(self, value):
        try:
            return float((value or "").strip())
        except Exception:
            return 0.0

    def _save(self):
        reg_no = self.reg_no_var.get().strip()
        batch_no = self.batch_no_var.get().strip()
        mfg_date = self.mfg_date_var.get().strip()
        exp_date = self.exp_date_var.get().strip()
        product_description = self.product_description_var.get().strip()

        quantity = self._to_float(self.quantity_var.get())
        trade_price = self._to_float(self.trade_price_var.get())
        discount_percent = self._to_float(self.discount_percent_var.get())

        if not reg_no or not batch_no or not mfg_date or not exp_date or not product_description:
            messagebox.showerror("Validation", "Please fill all required product fields.")
            return

        if quantity <= 0:
            messagebox.showerror("Validation", "Quantity must be greater than 0.")
            return

        if self.is_edit:
            update_inventory_item(
                item_id=self.item_id,
                reg_no=reg_no,
                batch_no=batch_no,
                mfg_date=mfg_date,
                exp_date=exp_date,
                quantity=quantity,
                product_description=product_description,
                trade_price=trade_price,
                discount_percent=discount_percent,
            )
            messagebox.showinfo("Success", "Product updated successfully.")
        else:
            save_inventory_item(
                reg_no=reg_no,
                batch_no=batch_no,
                mfg_date=mfg_date,
                exp_date=exp_date,
                quantity=quantity,
                product_description=product_description,
                trade_price=trade_price,
                discount_percent=discount_percent,
            )
            messagebox.showinfo("Success", "Product saved successfully.")
        self.on_saved()
        self.destroy()


class InventoryForm:
    def __init__(self, parent):
        self.parent = parent
        self._build()
        self._load_products()

    def _build(self):
        self.items_by_id = {}
        root = tk.Frame(self.parent, bg=COLORS["bg"])
        root.pack(fill="both", expand=True)

        card_outer = tk.Frame(root, bg=COLORS["border"])
        card_outer.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        card = tk.Frame(card_outer, bg=COLORS["card"])
        card.pack(fill="both", expand=True, padx=1, pady=1)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        head = tk.Frame(card, bg=COLORS["card"])
        head.grid(row=0, column=0, sticky="ew", padx=SPACING["xl"], pady=(SPACING["lg"], SPACING["md"]))
        tk.Label(head, text="Inventory", font=FONTS["section_header"], bg=COLORS["card"], fg=COLORS["text_dark"]).pack(
            side="left"
        )
        btns = tk.Frame(head, bg=COLORS["card"])
        btns.pack(side="right")
        tk.Button(btns, text="Add Product", command=self._open_add_product, **get_button_style("primary")).pack(
            side="right"
        )
        tk.Button(
            btns, text="Edit Product", command=self._open_edit_product, **get_button_style("secondary")
        ).pack(side="right", padx=(0, SPACING["sm"]))

        filters = tk.Frame(card, bg=COLORS["card"])
        filters.grid(row=1, column=0, sticky="ew", padx=SPACING["xl"], pady=(0, SPACING["md"]))
        filters.grid_columnconfigure(0, weight=1)
        filters.grid_columnconfigure(1, weight=1)
        filters.grid_columnconfigure(2, weight=1)
        filters.grid_columnconfigure(3, weight=0)

        self.search_reg_no_var = tk.StringVar()
        self.search_batch_no_var = tk.StringVar()
        self.search_product_name_var = tk.StringVar()

        self._search_field(filters, 0, "Reg No", self.search_reg_no_var)
        self._search_field(filters, 1, "Batch No", self.search_batch_no_var)
        self._search_field(filters, 2, "Product Name", self.search_product_name_var)

        actions = tk.Frame(filters, bg=COLORS["card"])
        actions.grid(row=1, column=3, sticky="e", padx=(SPACING["md"], 0))
        tk.Button(actions, text="Search", command=self._load_products, **get_button_style("secondary")).pack(side="left")
        tk.Button(actions, text="Clear", command=self._clear_filters, **get_button_style("secondary")).pack(
            side="left", padx=(SPACING["xs"], 0)
        )

        table_wrap = tk.Frame(card, bg=COLORS["card"])
        table_wrap.grid(row=2, column=0, sticky="nsew", padx=SPACING["xl"], pady=(0, SPACING["xl"]))
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")

        columns = ("Reg No", "Batch No", "Mfg Date", "Exp Date", "Qty", "Description", "Trade Price", "Discount %")
        self.table = ttk.Treeview(
            table_wrap,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set,
        )
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.table.yview)

        widths = {
            "Reg No": 120,
            "Batch No": 120,
            "Mfg Date": 110,
            "Exp Date": 110,
            "Qty": 80,
            "Description": 280,
            "Trade Price": 120,
            "Discount %": 110,
        }

        for col in columns:
            anchor = "e" if col in ("Qty", "Trade Price", "Discount %") else "w"
            self.table.heading(col, text=col, anchor=anchor)
            self.table.column(col, width=widths[col], minwidth=80, anchor=anchor)

        create_zebra_table(self.table)

    def _open_add_product(self):
        AddProductWindow(self.parent.winfo_toplevel(), self._load_products)

    def _open_edit_product(self):
        selection = self.table.selection()
        if not selection:
            messagebox.showerror("Selection Required", "Please select a product to edit.")
            return
        item_id = int(selection[0])
        data = self.items_by_id.get(item_id)
        if not data:
            messagebox.showerror("Error", "Could not load selected product.")
            return
        AddProductWindow(self.parent.winfo_toplevel(), self._load_products, item_id=item_id, initial_data=data)

    def _search_field(self, parent, col, label, variable):
        box = tk.Frame(parent, bg=COLORS["card"])
        box.grid(row=0, column=col, sticky="ew", padx=(0, SPACING["md"] if col < 2 else 0))
        tk.Label(box, text=label, font=FONTS["small"], bg=COLORS["card"], fg=COLORS["text_medium"]).pack(anchor="w")
        tk.Entry(box, textvariable=variable, **get_input_style()).pack(fill="x", ipady=4)

    def _clear_filters(self):
        self.search_reg_no_var.set("")
        self.search_batch_no_var.set("")
        self.search_product_name_var.set("")
        self._load_products()

    def _load_products(self):
        self.items_by_id = {}
        for item in self.table.get_children():
            self.table.delete(item)

        reg_q = (self.search_reg_no_var.get() or "").strip().lower()
        batch_q = (self.search_batch_no_var.get() or "").strip().lower()
        product_q = (self.search_product_name_var.get() or "").strip().lower()

        rows = list_inventory_items()
        visible_idx = 0
        for row in rows:
            item_id, reg_no, batch_no, mfg_date, exp_date, quantity, description, trade_price, discount_percent, _created = row
            reg_text = (reg_no or "").lower()
            batch_text = (batch_no or "").lower()
            product_text = (description or "").lower()

            if reg_q and reg_q not in reg_text:
                continue
            if batch_q and batch_q not in batch_text:
                continue
            if product_q and product_q not in product_text:
                continue

            self.items_by_id[item_id] = {
                "reg_no": reg_no or "",
                "batch_no": batch_no or "",
                "mfg_date": mfg_date or "",
                "exp_date": exp_date or "",
                "quantity": quantity or 0,
                "product_description": description or "",
                "trade_price": trade_price or 0,
                "discount_percent": discount_percent or 0,
            }

            tag = "evenrow" if visible_idx % 2 == 0 else "oddrow"
            self.table.insert(
                "",
                "end",
                iid=str(item_id),
                values=(
                    reg_no or "",
                    batch_no or "",
                    mfg_date or "",
                    exp_date or "",
                    f"{(quantity or 0):,.2f}",
                    description or "",
                    f"{(trade_price or 0):,.2f}",
                    f"{(discount_percent or 0):,.2f}",
                ),
                tags=(tag,),
            )
            visible_idx += 1
