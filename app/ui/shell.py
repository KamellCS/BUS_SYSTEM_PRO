"""Ventana principal: barra lateral, barra superior y área de contenido."""
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from .. import config, session, utils
from ..services import catalogos, ventas
from . import icons, theme as T
from .widgets import IconButton


# ====================================================================== barra lateral
class Sidebar(tk.Canvas):
    ANCHO, ANCHO_MINI, ALTO_ITEM = 268, 78, 52

    def __init__(self, parent, items, bottom, on_select):
        super().__init__(parent, width=self.ANCHO, highlightthickness=0, bd=0, bg=T.SIDEBAR_TOP)
        self.items, self.bottom, self.on_select = items, bottom, on_select
        self.activo, self.hover, self.mini = None, None, False
        self._hits, self._size = [], (0, 0)
        self.bind("<Configure>", lambda e: self.redraw(True))
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda e: self._set_hover(None))
        self.bind("<Button-1>", self._click)

    def set_activo(self, key):
        self.activo = key
        self.redraw()

    def toggle(self):
        self.mini = not self.mini
        self.configure(width=self.ANCHO_MINI if self.mini else self.ANCHO)
        self.redraw(True)

    def _color_en(self, y):
        H = max(self.winfo_height(), 1)
        return T.mix(T.SIDEBAR_TOP, T.SIDEBAR_BOTTOM, min(max(y / H, 0), 1))

    def redraw(self, fondo=False):
        W, H = self.winfo_width(), self.winfo_height()
        if W < 10:
            return
        if fondo or (W, H) != self._size:
            self.delete("all")
            icons.gradient(self, 0, 0, W, H, T.SIDEBAR_TOP, T.SIDEBAR_BOTTOM, tag="bg", step=3)
            self._size = (W, H)
        self.delete("fg")
        t = ("fg",)

        # logo
        icons.rounded_rect(self, 18, 20, 62, 64, r=12, fill=T.ACCENT, outline="", tags=t)
        icons.draw(self, "bus", 40, 42, 28, "#ffffff", tags=t, bg=T.ACCENT)
        if not self.mini:
            self.create_text(76, 34, text="BUS SYSTEM", anchor="w", fill="#ffffff",
                             font=T.font(15, "bold"), tags=t)
            self.create_text(76, 54, text="PRO", anchor="w", fill=T.ACCENT, font=T.font(10, "bold"), tags=t)
        self.create_line(18, 86, W - 18, 86, fill="#ffffff", stipple="gray25", tags=t)

        self._hits = []
        y = 102
        for key, texto, icono in self.items:
            if key == "_sep":
                if not self.mini:
                    self.create_text(24, y + 14, text=texto, anchor="w", fill="#8fb3d6",
                                     font=T.font(8, "bold"), tags=t)
                else:
                    self.create_line(24, y + 14, W - 24, y + 14, fill="#5d86b3", tags=t)
                y += 30
                continue
            self._item(key, texto, icono, y, W)
            y += self.ALTO_ITEM + 4
        yb = H - 20 - self.ALTO_ITEM
        for key, texto, icono in self.bottom:
            self._item(key, texto, icono, yb, W)
            yb -= self.ALTO_ITEM + 4

    def _item(self, key, texto, icono, y, W):
        t = ("fg",)
        activo, hover = key == self.activo, key == self.hover
        x1, x2 = 12, W - 12
        if activo:
            icons.rounded_rect(self, x1, y, x2, y + self.ALTO_ITEM, r=12, fill=T.ACCENT, outline="", tags=t)
            fondo = T.ACCENT
        elif hover:
            fondo = T.mix(self._color_en(y + 26), "#ffffff", .12)
            icons.rounded_rect(self, x1, y, x2, y + self.ALTO_ITEM, r=12, fill=fondo, outline="", tags=t)
        else:
            fondo = self._color_en(y + 26)
        cx = 40 if not self.mini else W / 2
        icons.draw(self, icono, cx, y + self.ALTO_ITEM / 2, 22, "#ffffff", tags=t, bg=fondo)
        if not self.mini:
            self.create_text(70, y + self.ALTO_ITEM / 2, text=texto.upper(), anchor="w", fill="#ffffff",
                             font=T.font(10, "bold"), tags=t)
        self._hits.append((y, y + self.ALTO_ITEM, key))

    def _key_en(self, y):
        for y1, y2, key in self._hits:
            if y1 <= y <= y2:
                return key
        return None

    def _motion(self, e):
        key = self._key_en(e.y)
        self.configure(cursor="hand2" if key else "")
        self._set_hover(key)

    def _set_hover(self, key):
        if key != self.hover:
            self.hover = key
            self.redraw()

    def _click(self, e):
        key = self._key_en(e.y)
        if key:
            self.on_select(key)


# ====================================================================== barra superior
class Topbar(tk.Frame):
    def __init__(self, parent, shell):
        super().__init__(parent, bg=T.SURFACE, height=66)
        self.pack_propagate(False)
        self.shell = shell
        IconButton(self, "menu", shell.sidebar.toggle, size=40).pack(side="left", padx=(18, 6))
        self.seccion = tk.Label(self, text="", bg=T.SURFACE, fg=T.MUTED, font=T.font(10, "bold"))
        self.seccion.pack(side="left", padx=6)

        u = session.usuario()
        # fecha
        fecha = tk.Frame(self, bg=T.SURFACE)
        fecha.pack(side="right", padx=(8, 24))
        cv = tk.Canvas(fecha, width=24, height=24, bg=T.SURFACE, highlightthickness=0)
        cv.pack(side="left")
        icons.draw(cv, "calendar", 12, 12, 18, T.MUTED)
        self.reloj = tk.Label(fecha, bg=T.SURFACE, fg=T.TEXT, font=T.font(10, "bold"))
        self.reloj.pack(side="left", padx=(6, 0))
        tk.Frame(self, bg=T.BORDER, width=1).pack(side="right", fill="y", pady=16, padx=8)

        # usuario
        usr = tk.Frame(self, bg=T.SURFACE)
        usr.pack(side="right", padx=8)
        av = tk.Canvas(usr, width=40, height=40, bg=T.SURFACE, highlightthickness=0)
        av.pack(side="left")
        color = T.PRIMARY if session.es_admin() else T.ACCENT_DARK
        av.create_oval(2, 2, 38, 38, fill=T.tint(color, .8), outline="")
        iniciales = (u["nombres"][:1] + u["apellidos"][:1]).upper()
        av.create_text(20, 21, text=iniciales, fill=color, font=T.font(11, "bold"))
        info = tk.Frame(usr, bg=T.SURFACE)
        info.pack(side="left", padx=(8, 0))
        rol = "Admin" if session.es_admin() else "Trabajador"
        tk.Label(info, text=f"{rol}: {session.nombre_corto()}", bg=T.SURFACE, fg=T.TEXT,
                 font=T.font(10, "bold")).pack(anchor="w")
        tk.Label(info, text=f"@{u['username']}", bg=T.SURFACE, fg=T.MUTED, font=T.font(8)).pack(anchor="w")

        self.campana = IconButton(self, "bell", self._notificaciones, size=40)
        self.campana.pack(side="right", padx=8)
        self.actualizar_badge()
        self._tick()

    def _tick(self):
        if not self.winfo_exists():
            return
        ahora = datetime.now()
        self.reloj.configure(text=f"{utils.fecha_larga(ahora.date())}  ·  {ahora:%H:%M}")
        self.after(20_000, self._tick)

    def actualizar_badge(self):
        pendientes = len(ventas.reservas_pendientes())
        mantenimiento = sum(1 for b in catalogos.listar_buses() if b["estado"] != "operativo")
        self.campana.set_badge(bool(pendientes or mantenimiento))

    def _notificaciones(self):
        reservas = ventas.reservas_pendientes()
        buses = [b for b in catalogos.listar_buses() if b["estado"] != "operativo"]
        lineas = []
        if reservas:
            lineas.append(f"• {len(reservas)} reservas pendientes de pago.")
            for r in reservas[:5]:
                lineas.append(f"     {utils.fecha_corta(r['fecha'])} {r['hora_salida']}  {r['ruta']}  "
                              f"asiento {r['asiento']} – {r['pasajero']}")
        if buses:
            lineas.append(f"• {len(buses)} bus(es) fuera de operación: "
                          + ", ".join(f"{b['unidad']} ({b['estado']})" for b in buses))
        messagebox.showinfo("Notificaciones", "\n".join(lineas) or "No hay notificaciones.",
                            parent=self)


# ====================================================================== vista base
class View(tk.Frame):
    titulo = ""
    subtitulo = ""

    def __init__(self, parent, shell, **kwargs):
        super().__init__(parent, bg=T.BG)
        self.shell = shell
        head = tk.Frame(self, bg=T.BG)
        head.pack(fill="x", padx=28, pady=(22, 14))
        izq = tk.Frame(head, bg=T.BG)
        izq.pack(side="left", fill="x", expand=True)
        self.lbl_titulo = tk.Label(izq, text=self.titulo, bg=T.BG, fg=T.TEXT, font=T.font(19, "bold"))
        self.lbl_titulo.pack(anchor="w")
        self.lbl_sub = tk.Label(izq, text=self.subtitulo, bg=T.BG, fg=T.MUTED, font=T.font(10))
        self.lbl_sub.pack(anchor="w")
        self.acciones = tk.Frame(head, bg=T.BG)
        self.acciones.pack(side="right")
        self.cuerpo = tk.Frame(self, bg=T.BG)
        self.cuerpo.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        self.build(**kwargs)

    def set_titulo(self, titulo, sub=None):
        self.lbl_titulo.configure(text=titulo)
        if sub is not None:
            self.lbl_sub.configure(text=sub)

    def build(self, **kwargs):
        raise NotImplementedError

    def error(self, e):
        messagebox.showerror("No se pudo completar", str(e), parent=self)

    def info(self, texto, titulo="Listo"):
        messagebox.showinfo(titulo, texto, parent=self)

    def confirmar(self, texto, titulo="Confirmar"):
        return messagebox.askyesno(titulo, texto, parent=self)


# ====================================================================== shell
class Shell(tk.Frame):
    def __init__(self, root, on_logout):
        super().__init__(root, bg=T.BG)
        self.on_logout = on_logout
        from .views import (asientos, buses, configuracion as v_conf, conductores, dashboard,
                            informes, pasajeros, rutas, usuarios, venta)
        self.vistas = {
            "dashboard": ("Tablero principal", "dashboard", dashboard.DashboardView, False),
            "venta": ("Venta de pasajes", "seat", venta.VentaView, False),
            "asientos": ("Mapa de asientos", "seats", asientos.AsientosView, False),
            "pasajeros": ("Registro de pasajeros", "idcard", pasajeros.PasajerosView, False),
            "rutas": ("Rutas y horarios", "route", rutas.RutasView, False),
            "buses": ("Gestión de buses", "bus", buses.BusesView, True),
            "conductores": ("Conductores", "driver", conductores.ConductoresView, True),
            "informes": ("Informes", "chart", informes.InformesView, True),
            "usuarios": ("Usuarios", "users", usuarios.UsuariosView, True),
            "config": ("Configuración", "gear", v_conf.ConfiguracionView, False),
        }
        items = []
        for key in ("dashboard", "venta", "asientos", "pasajeros", "rutas"):
            items.append((key, self.vistas[key][0], self.vistas[key][1]))
        if session.es_admin():
            items.append(("_sep", "ADMINISTRACIÓN", None))
            for key in ("buses", "conductores", "informes", "usuarios"):
                items.append((key, self.vistas[key][0], self.vistas[key][1]))
        items.append(("_sep", "SISTEMA", None))
        items.append(("config", "Configuración", "gear"))

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.sidebar = Sidebar(self, items, [("logout", "Cerrar sesión", "logout")], self.show)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="ns")
        self.topbar = Topbar(self, self)
        self.topbar.grid(row=0, column=1, sticky="ew")
        tk.Frame(self, bg=T.BORDER, height=1).grid(row=0, column=1, sticky="sew")
        self.content = tk.Frame(self, bg=T.BG)
        self.content.grid(row=1, column=1, sticky="nsew")
        self.actual = None
        self.show("dashboard")

    def show(self, key, **kwargs):
        if key == "logout":
            if messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar sesión?", parent=self):
                self.on_logout()
            return
        titulo, _icono, clase, solo_admin = self.vistas[key]
        if solo_admin and not session.es_admin():
            messagebox.showwarning("Acceso restringido", "Esta sección es solo para administradores.",
                                   parent=self)
            return
        if self.actual is not None:
            self.actual.destroy()
        self.actual = clase(self.content, self, **kwargs)
        self.actual.pack(fill="both", expand=True)
        self.sidebar.set_activo(key)
        self.topbar.seccion.configure(text=f"{config.APP_NAME}  /  {titulo}")
        self.topbar.actualizar_badge()
