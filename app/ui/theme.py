"""Paleta de colores, tipografía y estilos ttk."""
import tkinter as tk
from tkinter import ttk, font as tkfont

# ---- Paleta (inspirada en el diseño de referencia)
SIDEBAR_TOP = "#0b2b5a"
SIDEBAR_BOTTOM = "#0c5a86"
ACCENT = "#17b3c7"          # turquesa del ítem activo
ACCENT_DARK = "#1199ab"
ACCENT_SOFT = "#e2f6f9"
PRIMARY = "#1f5fd6"
PRIMARY_DARK = "#174bb0"
PRIMARY_SOFT = "#e8f0fd"
BG = "#eef3f9"
SURFACE = "#ffffff"
SURFACE_ALT = "#f6f9fc"
BORDER = "#dce4ee"
TEXT = "#10213a"
MUTED = "#6b7a90"
SUCCESS = "#22a35a"
SUCCESS_DARK = "#1b8a4b"
DANGER = "#e24646"
DANGER_DARK = "#c43535"
WARNING = "#f4a428"
ORANGE = "#f26b2a"
ORANGE_DARK = "#d9581b"

SEAT_FREE = "#2fb55d"
SEAT_SOLD = "#e04848"
SEAT_RESERVED = "#f4a62a"
SEAT_SELECTED = "#1f5fd6"

FAMILY = "Segoe UI"
_PREFERIDAS = ["Segoe UI", "Poppins", "Inter", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]


def font(size=10, weight="normal"):
    return (FAMILY, size, weight)


def mix(c1: str, c2: str, t: float) -> str:
    """Mezcla dos colores hex (t=0 → c1, t=1 → c2)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def tint(color: str, t=0.85) -> str:
    return mix(color, "#ffffff", t)


def shade(color: str, t=0.2) -> str:
    return mix(color, "#000000", t)


def init(root: tk.Tk):
    global FAMILY
    disponibles = set(tkfont.families(root))
    FAMILY = next((f for f in _PREFERIDAS if f in disponibles), "TkDefaultFont")

    root.configure(bg=BG)
    root.option_add("*Font", font(10))
    root.option_add("*TCombobox*Listbox.font", font(10))
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)

    st = ttk.Style(root)
    st.theme_use("clam")
    st.configure(".", font=font(10), background=SURFACE, foreground=TEXT)
    st.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=TEXT,
                 rowheight=32, borderwidth=0, font=font(10))
    st.configure("Treeview.Heading", background="#f2f6fb", foreground=MUTED, relief="flat",
                 font=font(9, "bold"), padding=(10, 8), borderwidth=0)
    st.map("Treeview", background=[("selected", ACCENT_SOFT)], foreground=[("selected", TEXT)])
    st.map("Treeview.Heading", background=[("active", "#e6edf6")])
    st.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    st.configure("TCombobox", padding=(8, 6), arrowsize=14, bordercolor=BORDER,
                 lightcolor=BORDER, darkcolor=BORDER, arrowcolor=MUTED)
    st.map("TCombobox", fieldbackground=[("readonly", SURFACE_ALT)],
           selectbackground=[("readonly", SURFACE_ALT)], selectforeground=[("readonly", TEXT)],
           bordercolor=[("focus", PRIMARY)])

    st.configure("Vertical.TScrollbar", background="#d5deea", troughcolor=SURFACE,
                 bordercolor=SURFACE, arrowcolor=MUTED, lightcolor="#d5deea", darkcolor="#d5deea")

    st.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(0, 0, 0, 0))
    st.configure("TNotebook.Tab", padding=(18, 9), font=font(10, "bold"),
                 background="#dfe7f2", foreground=MUTED, borderwidth=0)
    st.map("TNotebook.Tab", background=[("selected", SURFACE)], foreground=[("selected", PRIMARY)])
