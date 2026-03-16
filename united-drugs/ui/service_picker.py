import tkinter as tk
from tkinter import ttk
from services.service_service import list_services
from ui.theme import COLORS, FONTS, SPACING, get_button_style, create_zebra_table


class ServicePicker(tk.Toplevel):
    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.parent = parent
        self.on_select = on_select

        self.title("Select Service")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build()
        self._refresh()
        self._center()

    def _center(self):
        self.update_idletasks()
        w = 560
        h = 420
        x = self.winfo_screenwidth() // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        tk.Label(
            container,
            text="Select Service",
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
            columns=("Name", "Price"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("Name", text="Service", anchor="w")
        self.tree.heading("Price", text="Price", anchor="e")
        self.tree.column("Name", width=320, anchor="w")
        self.tree.column("Price", width=140, anchor="e")
        create_zebra_table(self.tree)

        self.tree.bind("<Double-1>", self._choose)

        self.empty_label = tk.Label(
            table,
            text="No services available. Ask admin to add services.",
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

        services = list_services()
        if not services:
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
            self.select_btn.config(state="disabled")
            return

        self.empty_label.place_forget()
        self.select_btn.config(state="normal")
        for idx, (service_id, name, price, _) in enumerate(services):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", iid=str(service_id), values=(name, f"{price:,.2f}"), tags=(tag,))

    def _choose(self, _=None):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        name = values[0]
        price = float(values[1].replace(",", ""))
        self.on_select(name, price)
        self.destroy()
