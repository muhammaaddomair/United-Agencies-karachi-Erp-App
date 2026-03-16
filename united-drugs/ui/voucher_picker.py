import tkinter as tk
from tkinter import ttk
from services.voucher_service import list_vouchers
from ui.theme import COLORS, FONTS, SPACING, get_button_style, create_zebra_table


class VoucherPicker(tk.Toplevel):
    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.parent = parent
        self.on_select = on_select

        self.title("Select Voucher")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build()
        self._refresh()
        self._center()

    def _center(self):
        self.update_idletasks()
        w = 620
        h = 420
        x = self.winfo_screenwidth() // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        tk.Label(
            container,
            text="Select Voucher",
            font=FONTS["section_header"],
            fg=COLORS["text_dark"],
            bg=COLORS["bg"]
        ).pack(anchor="w")

        table_outer = tk.Frame(container, bg=COLORS["border"])
        table_outer.pack(fill="both", expand=True, pady=(SPACING["lg"], 0))
        table = tk.Frame(table_outer, bg=COLORS["card"])
        table.pack(fill="both", expand=True, padx=1, pady=1)
        table.grid_rowconfigure(0, weight=1)
        table.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(table, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree = ttk.Treeview(
            table,
            columns=("Code", "Type", "Value"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("Code", text="Voucher Code", anchor="w")
        self.tree.heading("Type", text="Type", anchor="w")
        self.tree.heading("Value", text="Value", anchor="e")
        self.tree.column("Code", width=260, anchor="w")
        self.tree.column("Type", width=120, anchor="w")
        self.tree.column("Value", width=160, anchor="e")
        create_zebra_table(self.tree)

        self.tree.bind("<Double-1>", self._choose)

        self.empty_label = tk.Label(
            table,
            text="No vouchers available. Ask admin to add vouchers.",
            font=FONTS["body"],
            fg=COLORS["text_medium"],
            bg=COLORS["card"]
        )

        actions = tk.Frame(container, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(SPACING["lg"], 0))
        self.select_btn = tk.Button(actions, text="Select", command=self._choose, **get_button_style("primary"))
        self.select_btn.pack(side="left")
        tk.Button(actions, text="Cancel", command=self.destroy, **get_button_style("secondary")).pack(side="right")

    def _refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        vouchers = list_vouchers()
        if not vouchers:
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
            self.select_btn.config(state="disabled")
            return

        self.empty_label.place_forget()
        self.select_btn.config(state="normal")
        for idx, (voucher_id, code, discount_type, discount_value, _) in enumerate(vouchers):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            type_text = "Percent" if discount_type == "percent" else "Amount"
            value_text = f"{discount_value:,.2f}%" if discount_type == "percent" else f"{discount_value:,.2f}"
            self.tree.insert(
                "",
                "end",
                iid=str(voucher_id),
                values=(code, type_text, value_text),
                tags=(tag,)
            )

    def _choose(self, _=None):
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0], "values")
        code = values[0]
        type_text = values[1]
        discount_type = "percent" if type_text == "Percent" else "amount"
        discount_value = float(values[2].replace("%", "").replace(",", ""))
        self.on_select(code, discount_type, discount_value)
        self.destroy()
