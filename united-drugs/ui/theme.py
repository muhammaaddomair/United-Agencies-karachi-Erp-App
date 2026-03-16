from tkinter import ttk

COLORS = {
    # Primary Blue (Actions)
    "primary": "#4A90E2",
    "primary_hover": "#357ABD",
    "primary_light": "#E8F4FD",

    # Neutral Grays (Structure)
    "sidebar_dark": "#2C3E50",
    "text_dark": "#2D3436",
    "text_medium": "#636E72",
    "text_light": "#95A5A6",
    "border": "#DFE6E9",
    "divider": "#F0F0F0",

    # Backgrounds
    "bg": "#F8F9FA",
    "card": "#FFFFFF",
    "zebra": "#F9FAFB",
    "header_bg": "#F8F9FA",

    # Accent Colors
    "success": "#27AE60",
    "warning": "#F39C12",
    "error": "#E74C3C",
    "error_bg": "#FDEDEC",

    # Sidebar
    "sidebar_text": "#FFFFFF",
    "sidebar_border": "#34495E",
}

FONTS = {
    "page_title": ("Segoe UI", 22, "bold"),
    "section_header": ("Segoe UI", 16, "bold"),
    "body": ("Segoe UI", 13),
    "body_medium": ("Segoe UI", 13, "bold"),
    "label": ("Segoe UI", 12, "bold"),
    "small": ("Segoe UI", 11),
    "button": ("Segoe UI", 12, "bold"),

    "sidebar_brand": ("Segoe UI", 16, "bold"),
    "sidebar_menu": ("Segoe UI", 13),

    "table_header": ("Segoe UI", 12, "bold"),
    "table_body": ("Segoe UI", 12),
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "xxl": 48,
}

DIMENSIONS = {
    "table_row_height": 44,
    "header_height": 64,
    "sidebar_width": 220,
}


def apply_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background=COLORS["card"],
        foreground=COLORS["text_dark"],
        rowheight=DIMENSIONS["table_row_height"],
        fieldbackground=COLORS["card"],
        borderwidth=0,
        font=FONTS["table_body"]
    )

    style.configure(
        "Treeview.Heading",
        background=COLORS["header_bg"],
        foreground=COLORS["text_medium"],
        borderwidth=0,
        relief="flat",
        font=FONTS["table_header"],
        padding=[12, 10]
    )

    style.map(
        "Treeview",
        background=[("selected", COLORS["primary_light"])],
        foreground=[("selected", COLORS["text_dark"])]
    )


def create_zebra_table(tree):
    tree.tag_configure("oddrow", background=COLORS["card"])
    tree.tag_configure("evenrow", background=COLORS["zebra"])


def get_button_style(variant="primary"):
    styles = {
        "primary": {
            "bg": COLORS["primary"],
            "fg": "white",
            "activebackground": COLORS["primary_hover"],
            "activeforeground": "white",
            "relief": "flat",
            "cursor": "hand2",
            "font": FONTS["button"],
            "borderwidth": 0
        },
        "secondary": {
            "bg": COLORS["card"],
            "fg": COLORS["text_medium"],
            "activebackground": COLORS["bg"],
            "activeforeground": COLORS["text_dark"],
            "relief": "solid",
            "cursor": "hand2",
            "font": FONTS["button"],
            "borderwidth": 1,
            "highlightthickness": 1,
            "highlightbackground": COLORS["border"],
            "highlightcolor": COLORS["border"]
        },
        "success": {
            "bg": COLORS["success"],
            "fg": "white",
            "activebackground": "#229954",
            "activeforeground": "white",
            "relief": "flat",
            "cursor": "hand2",
            "font": FONTS["button"],
            "borderwidth": 0
        }
    }
    return styles.get(variant, styles["primary"])


def get_input_style():
    return {
        "bg": COLORS["card"],
        "fg": COLORS["text_dark"],
        "relief": "solid",
        "borderwidth": 1,
        "font": FONTS["body"],
        "insertbackground": COLORS["primary"],
        "highlightthickness": 1,
        "highlightbackground": COLORS["border"],
        "highlightcolor": COLORS["primary"]
    }
