"""Configuración: mi cuenta, datos de la empresa y base de datos."""
import tkinter as tk

from ... import config, session
from ...errors import AppError
from ...services import configuracion, usuarios, viajes
from .. import theme as T
from ..shell import View
from ..widgets import Badge, Button, Card, entry, label


class ConfiguracionView(View):
    titulo = "CONFIGURACIÓN"
    subtitulo = "Tu cuenta, datos de la empresa y mantenimiento de la base de datos"

    def build(self):
        c = self.cuerpo
        c.columnconfigure(0, weight=1, uniform="c")
        c.columnconfigure(1, weight=1, uniform="c")
        c.rowconfigure(1, weight=1)
        self._mi_cuenta(c)
        if session.es_admin():
            self._empresa(c)
            self._base_datos(c)
        else:
            card = Card(c, "ACERCA DEL SISTEMA")
            card.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
            label(card.body, f"{config.APP_NAME} v{config.APP_VERSION}\n{configuracion.obtener('empresa_nombre')}\n\n"
                             "Las opciones de empresa y base de datos solo están\ndisponibles para el administrador.",
                  weight="normal", justify="left").pack(anchor="w")

    def _form(self, parent, campos, valores=None, secreto=False):
        vars_ = {}
        for i, (k, titulo) in enumerate(campos):
            label(parent, titulo).grid(row=i * 2, column=0, sticky="w", pady=(10 if i else 0, 3))
            v = tk.StringVar(value=(valores or {}).get(k, ""))
            entry(parent, v, show="•" if secreto else None, width=40).grid(row=i * 2 + 1, column=0, sticky="ew", ipady=6)
            vars_[k] = v
        parent.columnconfigure(0, weight=1)
        return vars_

    def _mi_cuenta(self, c):
        u = session.usuario()
        card = Card(c, "MI CUENTA")
        card.grid(row=0, column=0, sticky="nsew")
        top = tk.Frame(card.body, bg=T.SURFACE)
        top.pack(fill="x")
        tk.Label(top, text=f"{u['nombres']} {u['apellidos']}", bg=T.SURFACE, fg=T.TEXT,
                 font=T.font(14, "bold")).pack(side="left")
        Badge(top, u["rol"]).pack(side="left", padx=10)
        label(card.body, f"Usuario: @{u['username']}", weight="normal").pack(anchor="w", pady=(2, 12))
        f = tk.Frame(card.body, bg=T.SURFACE)
        f.pack(fill="x")
        v = self._form(f, [("actual", "Contraseña actual"), ("nueva", "Nueva contraseña"),
                           ("conf", "Confirmar nueva contraseña")], secreto=True)

        def cambiar():
            try:
                usuarios.cambiar_mi_password(v["actual"].get(), v["nueva"].get(), v["conf"].get())
            except AppError as e:
                return self.error(e)
            for x in v.values():
                x.set("")
            self.info("Tu contraseña fue actualizada.")
        Button(card.body, "Cambiar contraseña", cambiar, "primary").pack(anchor="e", pady=(14, 0))

    def _empresa(self, c):
        card = Card(c, "DATOS DE LA EMPRESA")
        card.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        f = tk.Frame(card.body, bg=T.SURFACE)
        f.pack(fill="x")
        v = self._form(f, [("empresa_nombre", "Nombre comercial"), ("empresa_ruc", "RUC"),
                           ("empresa_telefono", "Teléfono"), ("empresa_direccion", "Dirección")],
                       configuracion.todo())

        def guardar():
            try:
                configuracion.guardar_empresa({k: x.get() for k, x in v.items()})
            except AppError as e:
                return self.error(e)
            self.info("Datos de la empresa guardados.")
        Button(card.body, "Guardar", guardar, "primary").pack(anchor="e", pady=(14, 0))

    def _base_datos(self, c):
        card = Card(c, "BASE DE DATOS")
        card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(16, 0))
        izq = tk.Frame(card.body, bg=T.SURFACE)
        izq.pack(side="left", fill="both", expand=True)
        label(izq, "ARCHIVO", size=8).pack(anchor="w")
        tk.Label(izq, text=str(config.DB_PATH), bg=T.SURFACE, fg=T.TEXT, font=T.font(9)).pack(anchor="w")
        label(izq, f"Tamaño: {configuracion.tamanio_bd_kb():,.0f} KB · Motor: SQLite", weight="normal").pack(
            anchor="w", pady=(2, 10))
        tabla = tk.Frame(izq, bg=T.SURFACE)
        tabla.pack(anchor="w")
        for i, (t, n) in enumerate(configuracion.estadisticas_bd()):
            caja = tk.Frame(tabla, bg=T.SURFACE_ALT, highlightthickness=1, highlightbackground=T.BORDER)
            caja.grid(row=0, column=i, padx=(0, 6), sticky="nsew")
            tk.Label(caja, text=f"{n:,}", bg=T.SURFACE_ALT, fg=T.PRIMARY, font=T.font(12, "bold"),
                     width=8).pack(pady=(6, 0))
            tk.Label(caja, text=t, bg=T.SURFACE_ALT, fg=T.MUTED, font=T.font(9)).pack(pady=(0, 6))

        der = tk.Frame(card.body, bg=T.SURFACE)
        der.pack(side="right", fill="y", padx=(20, 0))

        def respaldo():
            try:
                ruta = configuracion.crear_respaldo()
            except (AppError, OSError) as e:
                return self.error(e)
            self.info(f"Respaldo creado:\n{ruta}")

        def generar():
            n = viajes.programar_desde_horarios(config.DIAS_A_PROGRAMAR)
            self.info(f"{n} viajes nuevos generados." if n else "Los viajes ya estaban al día.")
        Button(der, "Crear respaldo de la BD", respaldo, "success").pack(fill="x")
        Button(der, f"Generar viajes ({config.DIAS_A_PROGRAMAR} días)", generar, "accent").pack(fill="x", pady=8)
        label(der, "Los respaldos se guardan en\ndata/backups/", weight="normal", justify="left").pack(anchor="w")
