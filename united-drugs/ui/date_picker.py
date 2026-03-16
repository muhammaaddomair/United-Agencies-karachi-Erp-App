import calendar
from datetime import datetime
import tkinter as tk
from ui.theme import COLORS, FONTS, SPACING, get_button_style


class DatePicker(tk.Toplevel):
    def __init__(self, parent, on_select, initial_date=None, anchor_widget=None):
        super().__init__(parent)
        self.parent = parent
        self.on_select = on_select
        self.anchor_widget = anchor_widget
        self.current = initial_date or datetime.now().date()

        self.overrideredirect(True)
        self.configure(bg=COLORS["border"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<FocusOut>", lambda _e: self.destroy())

        self._build()
        self._render()
        self._position()

    def _position(self):
        self.update_idletasks()
        w = 360
        h = 320

        if self.anchor_widget and self.anchor_widget.winfo_exists():
            x = self.anchor_widget.winfo_rootx()
            y = self.anchor_widget.winfo_rooty() + self.anchor_widget.winfo_height() + 2
            max_x = self.winfo_screenwidth() - w - 8
            max_y = self.winfo_screenheight() - h - 8
            if x > max_x:
                x = max_x
            if y > max_y:
                y = self.anchor_widget.winfo_rooty() - h - 2
            x = max(8, x)
            y = max(8, y)
        else:
            x = self.winfo_screenwidth() // 2 - w // 2
            y = self.winfo_screenheight() // 2 - h // 2

        self.geometry(f"{w}x{h}+{x}+{y}")
        self.lift()
        self.focus_force()

    def _build(self):
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(fill="both", expand=True, padx=1, pady=1)

        body = tk.Frame(container, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=SPACING["lg"], pady=SPACING["lg"])

        header = tk.Frame(body, bg=COLORS["bg"])
        header.pack(fill="x")

        tk.Button(
            header,
            text="<",
            command=self._prev_month,
            **get_button_style("secondary")
        ).pack(side="left")

        self.month_label = tk.Label(
            header,
            text="",
            font=FONTS["body_medium"],
            fg=COLORS["text_dark"],
            bg=COLORS["bg"]
        )
        self.month_label.pack(side="left", expand=True)

        tk.Button(
            header,
            text=">",
            command=self._next_month,
            **get_button_style("secondary")
        ).pack(side="right")

        self.grid_frame = tk.Frame(body, bg=COLORS["bg"])
        self.grid_frame.pack(fill="both", expand=True, pady=(SPACING["md"], 0))

        actions = tk.Frame(body, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(SPACING["md"], 0))
        tk.Button(actions, text="Close", command=self.destroy, **get_button_style("secondary")).pack(side="right")

    def _render(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        year = self.current.year
        month = self.current.month
        self.month_label.config(text=self.current.strftime("%B %Y"))

        days_header = tk.Frame(self.grid_frame, bg=COLORS["bg"])
        days_header.pack(fill="x")
        for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            tk.Label(
                days_header,
                text=d,
                font=FONTS["small"],
                fg=COLORS["text_medium"],
                bg=COLORS["bg"],
                width=4
            ).pack(side="left")

        cal = calendar.Calendar(firstweekday=0)
        for week in cal.monthdayscalendar(year, month):
            row = tk.Frame(self.grid_frame, bg=COLORS["bg"])
            row.pack(fill="x")
            for day in week:
                if day == 0:
                    tk.Label(row, text="", bg=COLORS["bg"], width=4).pack(side="left")
                    continue
                btn = tk.Button(
                    row,
                    text=str(day),
                    width=4,
                    command=lambda d=day: self._select_date(d),
                    **get_button_style("secondary")
                )
                btn.pack(side="left", padx=1, pady=1)

    def _select_date(self, day):
        selected = self.current.replace(day=day)
        self.on_select(selected.isoformat())
        self.destroy()

    def _prev_month(self):
        year = self.current.year
        month = self.current.month - 1
        if month < 1:
            month = 12
            year -= 1
        self.current = self.current.replace(year=year, month=month, day=1)
        self._render()

    def _next_month(self):
        year = self.current.year
        month = self.current.month + 1
        if month > 12:
            month = 1
            year += 1
        self.current = self.current.replace(year=year, month=month, day=1)
        self._render()
