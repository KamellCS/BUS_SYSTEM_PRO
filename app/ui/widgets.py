"""Componentes reutilizables: botones, tarjetas, tablas, formularios y mapa de asientos."""
import math
import tkinter as tk
from tkinter import ttk

from .. import utils
from ..errors import AppError
from . import icons, theme as T

# ====================================================================== botones
_ESTILOS_BOTON = {
    "primary": (T.PRIMARY, T.PRIMARY_DARK, "#ffffff"),
    "success": (T.SUCCESS, T.SUCCESS_DARK, "#ffffff"),
    "danger": (T.DANGER, T.DANGER_DARK, "#ffffff"),
    "orange": (T.ORANGE, T.ORANGE_DARK, "#ffffff"),
    "warning": (T.WARNING, "#d98b12", "#ffffff"),
    "accent": (T.ACCENT, T.ACCENT_DARK, "#ffffff"),
    "ghost": ("#e9eff7", "#dbe4f0", T.TEXT),
    "outline": (T.SURFACE, T.PRIMARY_SOFT, T.PRIMARY),
}


class Button(tk.Label):
    """Botón plano con hover. (tk.Label funciona igual en Windows, macOS y Linux)."""

    def __init__(self, parent, text, command=None, kind="primary", small=False, **kw):
        self._bg, self._hover, fg = _ESTILOS_BOTON[kind]
        super().__init__(parent, text=text, bg=self._bg, fg=fg, cursor="hand2",
                         font=T.font(9 if small else 10, "bold"),
                         padx=10 if small else 18, pady=4 if small else 9, **kw)
        if kind == "outline":
            self.configure(highlightthickness=1, highlightbackground=T.PRIMARY)
        self.command = command
        self.enabled = True
        self.bind("<Enter>", lambda e: self.enabled and self.configure(bg=self._hover))
        self.bind("<Leave>", lambda e: self.configure(bg=self._bg if self.enabled else "#c6d0dc"))
        self.bind("<ButtonRelease-1>", self._click)

    def _click(self, _e=None):
        if self.enabled and self.command:
            self.command()

    def set_enabled(self, valor: bool):
        self.enabled = valor
        self.configure(bg=self._bg if valor else "#c6d0dc", cursor="hand2" if valor else "arrow")


class IconButton(tk.Canvas):
    def __init__(self, parent, icon, command=None, size=36, color=T.MUTED, bg=T.SURFACE, badge=False):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, cursor="hand2")
        self._args = (icon, size, color, bg, badge)
        self.command = command
        self._dibujar(False)
        self.bind("<Enter>", lambda e: self._dibujar(True))
        self.bind("<Leave>", lambda e: self._dibujar(False))
        self.bind("<ButtonRelease-1>", lambda e: command and command())

    def _dibujar(self, hover):
        icon, size, color, bg, badge = self._args
        self.delete("all")
        if hover:
            self.create_oval(2, 2, size - 2, size - 2, fill="#eef3f9", outline="")
        icons.draw(self, icon, size / 2, size / 2, size * .5, T.PRIMARY if hover else color,
                   bg="#eef3f9" if hover else bg)
        if badge:
            self.create_oval(size * .62, size * .14, size * .82, size * .34, fill=T.DANGER, outline=bg, width=2)

    def set_badge(self, valor: bool):
        self._args = self._args[:4] + (valor,)
        self._dibujar(False)


# ====================================================================== contenedores
class Card(tk.Frame):
    """Tarjeta blanca con borde suave y título opcional."""

    def __init__(self, parent, title=None, padding=16, dots=True):
        super().__init__(parent, bg=T.SURFACE, highlightthickness=1, highlightbackground=T.BORDER)
        self.header = tk.Frame(self, bg=T.SURFACE)
        if title:
            self.header.pack(fill="x", padx=padding, pady=(padding - 2, 8))
            self.title_lbl = tk.Label(self.header, text=title, bg=T.SURFACE, fg=T.TEXT,
                                      font=T.font(11, "bold"))
            self.title_lbl.pack(side="left")
            if dots:
                tk.Label(self.header, text="•••", bg=T.SURFACE, fg="#a3b1c4",
                         font=T.font(9, "bold")).pack(side="right")
            self.actions = tk.Frame(self.header, bg=T.SURFACE)
            self.actions.pack(side="right", padx=(0, 8))
        self.body = tk.Frame(self, bg=T.SURFACE)
        self.body.pack(fill="both", expand=True, padx=padding, pady=(0 if title else padding, padding))

    def set_title(self, texto):
        self.title_lbl.configure(text=texto)


class StatCard(tk.Frame):
    """Tarjeta de indicador: título, valor grande, subtítulo e ícono."""

    def __init__(self, parent, title, value="—", icon="chart", color=T.PRIMARY, sub=""):
        super().__init__(parent, bg=T.SURFACE, highlightthickness=1, highlightbackground=T.BORDER)
        barra = tk.Frame(self, bg=color, width=4)
        barra.pack(side="left", fill="y")
        cv = tk.Canvas(self, width=58, height=58, bg=T.SURFACE, highlightthickness=0)
        cv.pack(side="right", padx=(4, 16))
        izq = tk.Frame(self, bg=T.SURFACE)
        izq.pack(side="left", fill="both", expand=True, padx=(16, 4), pady=14)
        tk.Label(izq, text=title.upper(), bg=T.SURFACE, fg=T.MUTED, font=T.font(9, "bold"),
                 anchor="w").pack(fill="x")
        self.value_lbl = tk.Label(izq, text=value, bg=T.SURFACE, fg=T.TEXT, anchor="w",
                                  font=T.font(self._tamanio(value), "bold"))
        self.value_lbl.pack(fill="x", pady=(2, 0))
        self.sub_lbl = tk.Label(izq, text=sub, bg=T.SURFACE, fg=T.MUTED, font=T.font(9), anchor="w")
        self.sub_lbl.pack(fill="x")
        fondo = T.tint(color, .85)
        cv.create_oval(3, 3, 55, 55, fill=fondo, outline="")
        icons.draw(cv, icon, 29, 29, 26, color, bg=fondo)

    @staticmethod
    def _tamanio(valor):
        return 19 if len(str(valor)) <= 10 else 16

    def set(self, value, sub=None):
        self.value_lbl.configure(text=value, font=T.font(self._tamanio(value), "bold"))
        if sub is not None:
            self.sub_lbl.configure(text=sub)


class Badge(tk.Label):
    COLORES = {
        "vendido": (T.SUCCESS, "Vendido"), "reservado": (T.WARNING, "Reservado"),
        "anulado": (T.MUTED, "Anulado"), "programado": (T.PRIMARY, "Programado"),
        "en_ruta": (T.ACCENT_DARK, "En ruta"), "finalizado": (T.MUTED, "Finalizado"),
        "cancelado": (T.DANGER, "Cancelado"), "operativo": (T.SUCCESS, "Operativo"),
        "mantenimiento": (T.WARNING, "Mantenimiento"), "fuera_servicio": (T.DANGER, "Fuera de servicio"),
        "libre": (T.SEAT_FREE, "Disponible"), "admin": (T.PRIMARY, "Administrador"),
        "trabajador": (T.ACCENT_DARK, "Trabajador"),
    }

    def __init__(self, parent, estado="", bg=T.SURFACE):
        super().__init__(parent, font=T.font(9, "bold"), padx=10, pady=3)
        self.set(estado)

    def set(self, estado):
        color, texto = self.COLORES.get(estado, (T.MUTED, estado.capitalize() if estado else ""))
        self.configure(text=texto, fg=color, bg=T.tint(color, .86))


def etiqueta_estado(estado: str) -> str:
    return Badge.COLORES.get(estado, (None, estado))[1]


class ScrollFrame(tk.Frame):
    """Frame con barra de desplazamiento vertical."""

    def __init__(self, parent, bg=T.BG):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.sb.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._rueda))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _rueda(self, e):
        self.canvas.yview_scroll(int(-e.delta / 120) or (-1 if e.delta > 0 else 1), "units")


# ====================================================================== tabla
class DataTable(tk.Frame):
    """Treeview con estilo, filas alternadas, orden por columna y selección simple.

    columns: lista de (clave, título, ancho, alineación)
    """

    def __init__(self, parent, columns, height=10, on_select=None, on_double=None):
        super().__init__(parent, bg=T.SURFACE, highlightthickness=1, highlightbackground=T.BORDER)
        self.columns = columns
        self.tree = ttk.Treeview(self, columns=[c[0] for c in columns], show="headings",
                                 height=height, selectmode="browse")
        for i, (key, titulo, ancho, anchor) in enumerate(columns):
            self.tree.heading(key, text=titulo, anchor=anchor, command=lambda k=key: self._ordenar(k))
            self.tree.column(key, width=ancho, minwidth=40, anchor=anchor, stretch=True)
        self.sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self._scroll)
        self.sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("par", background=T.SURFACE_ALT)
        self.tree.tag_configure("ok", foreground=T.SUCCESS_DARK)
        self.tree.tag_configure("warn", foreground="#b8730a")
        self.tree.tag_configure("bad", foreground=T.DANGER)
        self.tree.tag_configure("muted", foreground="#9aa6b6")
        self.tree.tag_configure("vacio", foreground=T.MUTED)
        self._rows = {}
        self._orden = {}
        if on_select:
            self.tree.bind("<<TreeviewSelect>>", lambda e: on_select(self.selected()))
        if on_double:
            self.tree.bind("<Double-1>", lambda e: self.selected() and on_double(self.selected()))

    def _scroll(self, first, last):
        """Muestra la barra de desplazamiento solo cuando hace falta."""
        self.sb.set(first, last)
        if float(first) <= 0 and float(last) >= 1:
            if self.sb.winfo_ismapped():
                self.sb.pack_forget()
        elif not self.sb.winfo_ismapped():
            self.sb.pack(side="right", fill="y", before=self.tree)

    def set_rows(self, rows, values, key="id", tag=None, vacio="Sin registros"):
        self.tree.delete(*self.tree.get_children())
        self._rows = {}
        for i, row in enumerate(rows):
            iid = str(row[key])
            self._rows[iid] = row
            tags = ["par"] if i % 2 else []
            if tag:
                t = tag(row)
                if t:
                    tags.append(t)
            self.tree.insert("", "end", iid=iid, values=values(row), tags=tags)
        if not rows and vacio:
            self.tree.insert("", "end", iid="__vacio__", values=(vacio,), tags=("vacio",))

    def selected(self):
        sel = self.tree.selection()
        return self._rows.get(sel[0]) if sel else None

    def select(self, key):
        key = str(key)
        if self.tree.exists(key):
            self.tree.selection_set(key)
            self.tree.focus(key)
            self.tree.see(key)

    def _ordenar(self, col):
        asc = not self._orden.get(col, False)
        self._orden = {col: asc}

        def clave(iid):
            v = self.tree.set(iid, col)
            limpio = v.replace("S/", "").replace(",", "").replace("%", "").strip()
            try:
                return (0, float(limpio))
            except ValueError:
                return (1, v.lower())

        items = sorted(self.tree.get_children(), key=clave, reverse=not asc)
        for i, iid in enumerate(items):
            self.tree.move(iid, "", i)
            tags = [t for t in self.tree.item(iid, "tags") if t != "par"]
            if i % 2:
                tags.append("par")
            self.tree.item(iid, tags=tags)


# ====================================================================== formularios
def entry(parent, var=None, show=None, width=28, readonly=False):
    e = tk.Entry(parent, textvariable=var, show=show or "", width=width, relief="flat",
                 bg=T.SURFACE_ALT, fg=T.TEXT, insertbackground=T.TEXT, font=T.font(10),
                 highlightthickness=1, highlightbackground=T.BORDER, highlightcolor=T.PRIMARY,
                 disabledbackground="#eef2f7", readonlybackground="#eef2f7")
    if readonly:
        e.configure(state="readonly")
    return e


def combo(parent, var, values, width=26):
    return ttk.Combobox(parent, textvariable=var, values=values, state="readonly",
                        width=width, font=T.font(10))


def label(parent, text, bg=T.SURFACE, fg=T.MUTED, size=9, weight="bold", **kw):
    return tk.Label(parent, text=text, bg=bg, fg=fg, font=T.font(size, weight), **kw)


def center(win, parent=None):
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    if parent is not None:
        top = parent.winfo_toplevel()
        x = top.winfo_rootx() + (top.winfo_width() - w) // 2
        y = top.winfo_rooty() + (top.winfo_height() - h) // 3
    else:
        x = (win.winfo_screenwidth() - w) // 2
        y = (win.winfo_screenheight() - h) // 3
    win.geometry(f"+{max(x, 0)}+{max(y, 0)}")


def modal(win, parent):
    win.transient(parent.winfo_toplevel())
    center(win, parent)
    try:
        win.wait_visibility()
        win.grab_set()
    except tk.TclError:
        pass
    win.focus_set()


class FormDialog(tk.Toplevel):
    """Formulario modal genérico.

    fields: lista de dicts con: key, label, type ('text'|'password'|'combo'|'readonly'),
            options (lista de str o de (valor, texto)), required (bool)
    on_submit(data) debe lanzar AppError si algo está mal.
    """

    def __init__(self, parent, title, fields, initial=None, on_submit=None,
                 submit_text="Guardar", subtitle=None):
        super().__init__(parent)
        self.withdraw()
        self.title(title)
        self.configure(bg=T.SURFACE)
        self.resizable(False, False)
        self.on_submit = on_submit
        self.result = None
        initial = initial or {}

        head = tk.Frame(self, bg=T.PRIMARY)
        head.pack(fill="x")
        tk.Label(head, text=title, bg=T.PRIMARY, fg="#ffffff", font=T.font(13, "bold")).pack(
            anchor="w", padx=22, pady=(14, 0 if subtitle else 14))
        if subtitle:
            tk.Label(head, text=subtitle, bg=T.PRIMARY, fg="#cfe0ff", font=T.font(9)).pack(
                anchor="w", padx=22, pady=(0, 12))

        body = tk.Frame(self, bg=T.SURFACE)
        body.pack(fill="both", padx=22, pady=(10, 4))
        cols = 2 if len(fields) > 4 else 1
        self.vars, self._maps, primero = {}, {}, None
        for i, f in enumerate(fields):
            r, c = divmod(i, cols)
            if f.get("full"):
                c = 0
            padx = (0, 0) if c == 0 else (16, 0)
            texto = f["label"] + ("  *" if f.get("required") else "")
            label(body, texto).grid(row=r * 2, column=c, sticky="w", padx=padx, pady=(10, 3))
            var = tk.StringVar()
            valor = initial.get(f["key"], f.get("default", ""))
            tipo = f.get("type", "text")
            if tipo == "combo":
                opciones = f.get("options", [])
                if opciones and isinstance(opciones[0], (tuple, list)):
                    mapa = {str(t): v for v, t in opciones}
                    self._maps[f["key"]] = mapa
                    textos = list(mapa)
                    inv = {str(v): t for t, v in mapa.items()}
                    var.set(inv.get(str(valor), ""))
                else:
                    textos = [str(o) for o in opciones]
                    var.set("" if valor is None else str(valor))
                w = combo(body, var, textos, width=f.get("width", 27))
                w.grid(row=r * 2 + 1, column=c, sticky="we", padx=padx)
            else:
                var.set("" if valor is None else str(valor))
                w = entry(body, var, show="•" if tipo == "password" else None,
                          width=f.get("width", 30), readonly=(tipo == "readonly"))
                w.grid(row=r * 2 + 1, column=c, sticky="we", padx=padx, ipady=6)
                if primero is None and tipo != "readonly":
                    primero = w
            self.vars[f["key"]] = var

        self.error = tk.Label(body, text="", bg=T.SURFACE, fg=T.DANGER, font=T.font(9, "bold"),
                              wraplength=520, justify="left")
        self.error.grid(row=999, column=0, columnspan=2, sticky="w", pady=(12, 0))

        foot = tk.Frame(self, bg=T.SURFACE)
        foot.pack(fill="x", padx=22, pady=(8, 18))
        Button(foot, submit_text, self._enviar, "primary").pack(side="right")
        Button(foot, "Cancelar", self.destroy, "ghost").pack(side="right", padx=8)

        self.bind("<Return>", lambda e: self._enviar())
        self.bind("<Escape>", lambda e: self.destroy())
        self.deiconify()
        modal(self, parent)
        if primero is not None:
            primero.focus_set()

    def datos(self):
        salida = {}
        for k, var in self.vars.items():
            v = var.get().strip()
            if k in self._maps:
                v = self._maps[k].get(v, "")
            salida[k] = v
        return salida

    def _enviar(self):
        data = self.datos()
        try:
            if self.on_submit:
                self.on_submit(data)
        except AppError as e:
            self.error.configure(text="⚠  " + str(e))
            return
        self.result = data
        self.destroy()


# ====================================================================== mapa de asientos
class Legend(tk.Frame):
    def __init__(self, parent, bg=T.SURFACE, vertical=True, seleccion=True):
        super().__init__(parent, bg=bg)
        items = [("Disponible", T.SEAT_FREE), ("Ocupado", T.SEAT_SOLD), ("Reservado", T.SEAT_RESERVED)]
        if seleccion:
            items.append(("Seleccionado", T.SEAT_SELECTED))
        for i, (texto, color) in enumerate(items):
            f = tk.Frame(self, bg=bg)
            if vertical:
                f.pack(anchor="w", pady=4)
            else:
                f.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 18), pady=2)
            cv = tk.Canvas(f, width=20, height=20, bg=bg, highlightthickness=0)
            cv.pack(side="left")
            icons.rounded_rect(cv, 2, 2, 18, 18, r=4, fill=color, outline="")
            tk.Label(f, text=texto, bg=bg, fg=T.TEXT, font=T.font(10)).pack(side="left", padx=6)


class SeatMap(tk.Canvas):
    """Plano del bus con asientos 2 + pasillo + 2.

    mode='sell'    → clic en asiento libre lo selecciona; clic en ocupado llama on_info.
    mode='inspect' → clic en cualquier asiento lo marca y llama on_select.
    """

    def __init__(self, parent, mode="sell", on_select=None, on_info=None, bg=T.SURFACE):
        super().__init__(parent, bg=bg, highlightthickness=0, width=300, height=420)
        self.mode = mode
        self.on_select = on_select
        self.on_info = on_info
        self._bg = bg
        self.capacidad = 0
        self.ocupados = {}
        self.selected = None
        self.mensaje = "Selecciona un viaje"
        self.bind("<Configure>", lambda e: self.redraw())

    def load(self, capacidad, ocupados: dict, selected=None):
        self.capacidad = capacidad or 0
        self.ocupados = ocupados or {}
        self.selected = selected
        self.redraw()

    def clear(self, mensaje="Selecciona un viaje"):
        self.capacidad, self.ocupados, self.selected, self.mensaje = 0, {}, None, mensaje
        self.redraw()

    def estado(self, n):
        b = self.ocupados.get(n)
        return b["estado"] if b else "libre"

    def redraw(self):
        self.delete("all")
        W, H = self.winfo_width(), self.winfo_height()
        if W < 50 or H < 50:
            return
        if not self.capacidad:
            icons.draw(self, "bus", W / 2, H / 2 - 24, 44, "#c3cede", bg=self._bg)
            self.create_text(W / 2, H / 2 + 28, text=self.mensaje, fill=T.MUTED, font=T.font(10))
            return

        filas = math.ceil(self.capacidad / 4)
        cabina = 62
        borde = 16
        disponible_h = H - 20 - cabina - borde
        seat = int(max(16, min(40, disponible_h / filas - 6)))
        gap = max(4, seat // 6)
        pasillo = int(seat * .75)
        ancho = 4 * seat + 3 * gap + pasillo + 2 * borde
        alto = cabina + filas * (seat + gap) + borde
        x0 = (W - ancho) / 2
        y0 = (H - alto) / 2

        # carrocería
        icons.rounded_rect(self, x0 - 6, y0 + 20, x0 + 2, y0 + 44, r=3, fill="#9aa8bb", outline="")
        icons.rounded_rect(self, x0 + ancho - 2, y0 + 20, x0 + ancho + 6, y0 + 44, r=3, fill="#9aa8bb", outline="")
        icons.rounded_rect(self, x0, y0, x0 + ancho, y0 + alto, r=30, fill="#f3f6fa", outline="#c2cddb", width=2)
        icons.rounded_rect(self, x0 + 14, y0 + 6, x0 + ancho - 14, y0 + 14, r=4, fill="#cbd6e4", outline="")
        # conductor
        self.create_oval(x0 + borde + 2, y0 + 20, x0 + borde + 38, y0 + 56, fill=T.tint(T.PRIMARY, .8), outline="")
        icons.draw(self, "person", x0 + borde + 20, y0 + 40, 26, T.PRIMARY, bg=T.tint(T.PRIMARY, .8))
        # puerta / escalera
        icons.draw(self, "stairs", x0 + ancho - borde - 16, y0 + 36, 22, "#8796ab", bg="#f3f6fa")
        self.create_line(x0 + 10, y0 + cabina - 8, x0 + ancho - 10, y0 + cabina - 8, fill="#d6dee9", dash=(4, 3))

        for n in range(1, self.capacidad + 1):
            fila, col = divmod(n - 1, 4)
            sx = x0 + borde + col * (seat + gap) + (pasillo if col >= 2 else 0)
            sy = y0 + cabina + fila * (seat + gap)
            est = self.estado(n)
            color = {"libre": T.SEAT_FREE, "vendido": T.SEAT_SOLD, "reservado": T.SEAT_RESERVED}[est]
            if self.mode == "sell" and n == self.selected:
                color = T.SEAT_SELECTED
            tag = f"s{n}"
            icons.rounded_rect(self, sx, sy, sx + seat, sy + seat, r=max(4, seat // 5), fill=color,
                               outline=T.shade(color, .15), tags=(tag,))
            self.create_rectangle(sx + 4, sy + 3, sx + seat - 4, sy + max(5, seat // 6), fill=T.shade(color, .18),
                                  outline="", tags=(tag,))
            self.create_text(sx + seat / 2, sy + seat / 2 + 2, text=str(n), fill="#ffffff",
                             font=T.font(max(7, seat // 3 - 1), "bold"), tags=(tag,))
            if self.mode == "inspect" and n == self.selected:
                icons.rounded_rect(self, sx - 3, sy - 3, sx + seat + 3, sy + seat + 3, r=8, fill="",
                                   outline=T.SEAT_SELECTED, width=3, tags=(tag,))
            self.tag_bind(tag, "<Button-1>", lambda e, k=n: self._click(k))
            self.tag_bind(tag, "<Enter>", lambda e: self.configure(cursor="hand2"))
            self.tag_bind(tag, "<Leave>", lambda e: self.configure(cursor=""))

        if self.selected:
            fila, col = divmod(self.selected - 1, 4)
            sx = x0 + borde + col * (seat + gap) + (pasillo if col >= 2 else 0)
            sy = y0 + cabina + fila * (seat + gap)
            texto = f"Asiento {self.selected} ({utils.posicion_asiento(self.selected)})"
            bw = 168
            by = sy + seat / 2 - 15
            if x0 + ancho + bw + 14 < W:          # globo a la derecha del bus
                bx = x0 + ancho + 10
            elif x0 - bw - 10 > 0:                 # o a la izquierda
                bx = x0 - bw - 10
            else:                                  # sin espacio: no se dibuja
                return
            icons.rounded_rect(self, bx, by, bx + bw, by + 30, r=8, fill="#ffffff", outline="#c2cddb")
            self.create_text(bx + bw / 2, by + 15, text=texto, fill=T.TEXT, font=T.font(9, "bold"))

    def _click(self, n):
        est = self.estado(n)
        if self.mode == "inspect":
            self.selected = n
            self.redraw()
            if self.on_select:
                self.on_select(n)
            return
        if est != "libre":
            if self.on_info:
                self.on_info(n, self.ocupados.get(n))
            return
        self.selected = None if self.selected == n else n
        self.redraw()
        if self.on_select:
            self.on_select(self.selected)


# ====================================================================== gráfico de barras
class BarChart(tk.Canvas):
    def __init__(self, parent, height=230, color=T.ACCENT):
        super().__init__(parent, bg=T.SURFACE, highlightthickness=0, height=height)
        self.data = []
        self.color = color
        self.bind("<Configure>", lambda e: self.redraw())

    def load(self, data):
        self.data = data
        self.redraw()

    def redraw(self):
        self.delete("all")
        W, H = self.winfo_width(), self.winfo_height()
        if W < 60 or not self.data:
            return
        izq, der, arriba, abajo = 64, 12, 22, 30
        maximo = max((v for _, v in self.data), default=0) or 1
        crudo = maximo / 5                                   # escala "bonita": 1, 2, 2.5, 5, 10
        magnitud = 10 ** math.floor(math.log10(crudo)) if crudo > 0 else 1
        paso = next(m * magnitud for m in (1, 2, 2.5, 5, 10) if crudo <= m * magnitud)
        lineas = max(1, math.ceil(maximo / paso))
        tope = paso * lineas
        for i in range(lineas + 1):
            y = H - abajo - (H - arriba - abajo) * i / lineas
            self.create_line(izq, y, W - der, y, fill="#edf1f6")
            self.create_text(izq - 8, y, text=utils.dinero_corto(paso * i), anchor="e",
                             fill=T.MUTED, font=T.font(8))
        n = len(self.data)
        ancho = (W - izq - der) / n
        barra = max(6, min(46, ancho * .62))
        mostrar_cada = max(1, math.ceil(n / 16))
        for i, (etq, v) in enumerate(self.data):
            cx = izq + ancho * i + ancho / 2
            h = (H - arriba - abajo) * (v / tope)
            y = H - abajo - h
            color = T.PRIMARY if i == n - 1 else self.color
            if h > 0:
                icons.rounded_rect(self, cx - barra / 2, y, cx + barra / 2, H - abajo, r=min(6, barra / 3),
                                   fill=color, outline="")
            if ancho >= 50 and v:
                self.create_text(cx, y - 9, text=utils.dinero_corto(v), fill=T.TEXT, font=T.font(8, "bold"))
            if i % mostrar_cada == 0 or i == n - 1:
                self.create_text(cx, H - abajo + 14, text=etq, fill=T.MUTED, font=T.font(8))


class ProgressBar(tk.Canvas):
    def __init__(self, parent, height=10, color=T.ACCENT, bg=T.SURFACE):
        super().__init__(parent, height=height, bg=bg, highlightthickness=0)
        self.valor, self.color = 0, color
        self.bind("<Configure>", lambda e: self.redraw())

    def set(self, valor):
        self.valor = max(0.0, min(1.0, valor))
        self.redraw()

    def redraw(self):
        self.delete("all")
        W, H = self.winfo_width(), self.winfo_height()
        icons.rounded_rect(self, 0, 0, W, H, r=H / 2, fill="#e6ecf4", outline="")
        if self.valor > 0:
            icons.rounded_rect(self, 0, 0, max(H, W * self.valor), H, r=H / 2, fill=self.color, outline="")
