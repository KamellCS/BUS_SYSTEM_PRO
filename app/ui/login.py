"""Pantalla de inicio de sesión (administrador / trabajador)."""
import tkinter as tk

from .. import config
from ..errors import AppError
from ..services import auth, configuracion
from . import icons, theme as T
from .widgets import Button


class LoginView(tk.Frame):
    def __init__(self, root, on_success):
        super().__init__(root, bg=T.SURFACE)
        self.on_success = on_success
        self.rol = tk.StringVar(value="admin")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0, minsize=500)
        self.rowconfigure(0, weight=1)

        # ---------------- panel izquierdo (marca)
        self.hero = tk.Canvas(self, highlightthickness=0, bg=T.SIDEBAR_TOP)
        self.hero.grid(row=0, column=0, sticky="nsew")
        self.hero.bind("<Configure>", lambda e: self._dibujar_hero())

        # ---------------- panel derecho (formulario)
        der = tk.Frame(self, bg=T.SURFACE)
        der.grid(row=0, column=1, sticky="nsew")
        caja = tk.Frame(der, bg=T.SURFACE)
        caja.place(relx=.5, rely=.5, anchor="center", width=380)

        logo = tk.Canvas(caja, width=56, height=56, bg=T.SURFACE, highlightthickness=0)
        logo.pack(anchor="w")
        icons.rounded_rect(logo, 2, 2, 54, 54, r=14, fill=T.SIDEBAR_TOP, outline="")
        icons.draw(logo, "bus", 28, 28, 32, T.ACCENT, bg=T.SIDEBAR_TOP)

        tk.Label(caja, text="Bienvenido", bg=T.SURFACE, fg=T.TEXT,
                 font=T.font(24, "bold")).pack(anchor="w", pady=(18, 0))
        tk.Label(caja, text="Ingresa con tu cuenta para continuar", bg=T.SURFACE, fg=T.MUTED,
                 font=T.font(10)).pack(anchor="w", pady=(2, 20))

        # selector de rol
        seg = tk.Frame(caja, bg="#e9eff7")
        seg.pack(fill="x", ipady=3)
        self._tabs = {}
        for valor, texto in (("admin", "Administrador"), ("trabajador", "Trabajador")):
            lbl = tk.Label(seg, text=texto, font=T.font(10, "bold"), cursor="hand2", pady=8)
            lbl.pack(side="left", fill="x", expand=True, padx=3, pady=3)
            lbl.bind("<Button-1>", lambda e, v=valor: self._set_rol(v))
            self._tabs[valor] = lbl
        self._set_rol("admin")

        self.usuario = self._campo(caja, "Usuario", "person")
        self.password = self._campo(caja, "Contraseña", "lock", secreto=True)

        self.error = tk.Label(caja, text="", bg=T.SURFACE, fg=T.DANGER, font=T.font(9, "bold"),
                              wraplength=370, justify="left")
        self.error.pack(anchor="w", pady=(10, 0))

        self.btn = Button(caja, "Ingresar al sistema", self._ingresar, "primary")
        self.btn.configure(pady=12, font=T.font(11, "bold"))
        self.btn.pack(fill="x", pady=(12, 18))

        demo = tk.Frame(caja, bg=T.ACCENT_SOFT, highlightthickness=1, highlightbackground="#bfe9ef")
        demo.pack(fill="x")
        tk.Label(demo, text="Cuentas de prueba  (clic para autocompletar)", bg=T.ACCENT_SOFT,
                 fg=T.ACCENT_DARK, font=T.font(9, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        for rol, user, pwd in (("admin", "admin", "admin123"), ("trabajador", "vendedor", "vendedor123")):
            fila = tk.Label(demo, text=f"{'Administrador' if rol == 'admin' else 'Trabajador'}:  "
                                       f"{user}  /  {pwd}",
                            bg=T.ACCENT_SOFT, fg=T.TEXT, font=T.font(9), cursor="hand2")
            fila.pack(anchor="w", padx=12, pady=(0, 2))
            fila.bind("<Button-1>", lambda e, r=rol, u=user, p=pwd: self._autocompletar(r, u, p))
        tk.Frame(demo, bg=T.ACCENT_SOFT, height=8).pack()

        tk.Label(der, text=f"© 2026 {configuracion.obtener('empresa_nombre')} · v{config.APP_VERSION}",
                 bg=T.SURFACE, fg="#9aa6b6", font=T.font(8)).place(relx=.5, rely=.97, anchor="s")

        self.usuario.focus_set()
        root.bind("<Return>", self._ingresar)

    # ------------------------------------------------------------------ partes
    def _campo(self, parent, titulo, icono, secreto=False):
        tk.Label(parent, text=titulo, bg=T.SURFACE, fg=T.MUTED, font=T.font(9, "bold")).pack(
            anchor="w", pady=(16, 4))
        marco = tk.Frame(parent, bg=T.SURFACE_ALT, highlightthickness=1, highlightbackground=T.BORDER,
                         highlightcolor=T.PRIMARY)
        marco.pack(fill="x")
        cv = tk.Canvas(marco, width=40, height=40, bg=T.SURFACE_ALT, highlightthickness=0)
        cv.pack(side="left")
        icons.draw(cv, icono, 21, 21, 18, "#8a99ad", bg=T.SURFACE_ALT)
        e = tk.Entry(marco, relief="flat", bg=T.SURFACE_ALT, fg=T.TEXT, font=T.font(11),
                     insertbackground=T.TEXT, show="•" if secreto else "", highlightthickness=0)
        e.pack(side="left", fill="x", expand=True, ipady=8)
        if secreto:
            ver = tk.Label(marco, text="Ver", bg=T.SURFACE_ALT, fg=T.PRIMARY, font=T.font(9, "bold"),
                           cursor="hand2", padx=12)
            ver.pack(side="right")

            def alternar(_e=None):
                oculto = e.cget("show") == "•"
                e.configure(show="" if oculto else "•")
                ver.configure(text="Ocultar" if oculto else "Ver")
            ver.bind("<Button-1>", alternar)
        e.bind("<FocusIn>", lambda ev: marco.configure(highlightbackground=T.PRIMARY))
        e.bind("<FocusOut>", lambda ev: marco.configure(highlightbackground=T.BORDER))
        return e

    def _set_rol(self, valor):
        self.rol.set(valor)
        for v, lbl in self._tabs.items():
            activo = v == valor
            lbl.configure(bg=T.SURFACE if activo else "#e9eff7", fg=T.PRIMARY if activo else T.MUTED)

    def _autocompletar(self, rol, user, pwd):
        self._set_rol(rol)
        for e, v in ((self.usuario, user), (self.password, pwd)):
            e.delete(0, "end")
            e.insert(0, v)
        self.error.configure(text="")

    def _ingresar(self, _e=None):
        try:
            auth.login(self.usuario.get(), self.password.get(), self.rol.get())
        except AppError as e:
            self.error.configure(text="⚠  " + str(e))
            self.password.delete(0, "end")
            self.password.focus_set()
            return
        self.winfo_toplevel().unbind("<Return>")
        self.on_success()

    # ------------------------------------------------------------------ arte
    def _dibujar_hero(self):
        cv = self.hero
        cv.delete("all")
        W, H = cv.winfo_width(), cv.winfo_height()
        if W < 100:
            return
        icons.gradient(cv, 0, 0, W, H, T.SIDEBAR_TOP, "#0e7ea3", step=4)
        # círculos decorativos
        for (cx, cy, r, c) in ((W * .9, H * .12, 180, "#2a6d9c"), (W * .05, H * .95, 240, "#1f6492"),
                               (W * .75, H * .82, 90, "#2a86ad")):
            cv.create_oval(cx - r, cy - r, cx + r, cy + r, outline=c, width=2)

        # marca
        x = W * .1
        cv.create_text(x, H * .14, text=config.APP_NAME, anchor="w", fill="#ffffff",
                       font=T.font(30, "bold"))
        cv.create_text(x, H * .14 + 42, text="Venta de pasajes y gestión de flota",
                       anchor="w", fill="#bfe3f0", font=T.font(13))
        cv.create_line(x, H * .14 + 72, x + 60, H * .14 + 72, fill=T.ACCENT, width=4)

        # carretera + bus
        ancho_bus = min(W * .72, 560)
        bx = (W - ancho_bus) / 2
        by = H * .40
        h = ancho_bus * .42
        suelo = by + h * .98 + ancho_bus * .075 * 1.25
        cv.create_rectangle(0, suelo, W, suelo + 46, fill="#0a2547", outline="")
        for i in range(0, int(W) + 80, 80):
            cv.create_line(i, suelo + 23, i + 40, suelo + 23, fill="#f5c84a", width=4)
        cv.create_oval(bx + ancho_bus * .05, suelo - 10, bx + ancho_bus * .95, suelo + 8,
                       fill="#08203f", outline="")
        icons.draw_bus_side(cv, bx, by, ancho_bus, glass="#0b2b5a")
        cv.create_text(bx + ancho_bus * .43, by + h * .82, text=config.APP_NAME, fill=T.SIDEBAR_TOP,
                       font=T.font(max(8, int(ancho_bus / 40)), "bold"))

        # beneficios
        y = suelo + 90
        for texto, icono in (("Venta de pasajes en segundos", "ticket"),
                             ("Mapa de asientos en tiempo real", "seats"),
                             ("Control de flota, rutas e informes", "chart")):
            if y > H - 30:
                break
            cv.create_oval(x, y - 16, x + 32, y + 16, fill="#1d6a98", outline="")
            icons.draw(cv, icono, x + 16, y, 16, "#ffffff", bg="#1d6a98")
            cv.create_text(x + 46, y, text=texto, anchor="w", fill="#e6f4fa", font=T.font(11))
            y += 46
