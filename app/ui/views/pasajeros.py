"""Registro de pasajeros."""
import tkinter as tk

from ... import config, session, utils
from ...errors import AppError
from ...services import ventas
from .. import icons, theme as T
from ..shell import View
from ..widgets import Button, Card, DataTable, FormDialog, modal

CAMPOS = [
    {"key": "tipo_doc", "label": "Tipo de documento", "type": "combo", "options": config.TIPOS_DOC,
     "default": "DNI", "required": True},
    {"key": "num_doc", "label": "Número de documento", "required": True},
    {"key": "nombres", "label": "Nombres", "required": True},
    {"key": "apellidos", "label": "Apellidos", "required": True},
    {"key": "telefono", "label": "Teléfono"},
    {"key": "email", "label": "Correo electrónico"},
]


class PasajerosView(View):
    titulo = "REGISTRO DE PASAJEROS"
    subtitulo = "Base de clientes de la empresa con su historial de viajes"

    def build(self):
        Button(self.acciones, "+  Nuevo pasajero", self._nuevo, "primary").pack(side="right")

        card = Card(self.cuerpo, dots=False)
        card.pack(fill="both", expand=True)
        barra = tk.Frame(card.body, bg=T.SURFACE)
        barra.pack(fill="x", pady=(0, 12))
        caja = tk.Frame(barra, bg=T.SURFACE_ALT, highlightthickness=1, highlightbackground=T.BORDER)
        caja.pack(side="left")
        cv = tk.Canvas(caja, width=36, height=36, bg=T.SURFACE_ALT, highlightthickness=0)
        cv.pack(side="left")
        icons.draw(cv, "search", 19, 18, 16, T.MUTED, bg=T.SURFACE_ALT)
        self.var_buscar = tk.StringVar()
        e = tk.Entry(caja, textvariable=self.var_buscar, relief="flat", bg=T.SURFACE_ALT, width=38,
                     font=T.font(10), highlightthickness=0)
        e.pack(side="left", ipady=6, padx=(0, 10))
        self.var_buscar.trace_add("write", lambda *a: self._cargar())
        self.lbl_total = tk.Label(barra, text="", bg=T.SURFACE, fg=T.MUTED, font=T.font(9))
        self.lbl_total.pack(side="left", padx=14)

        botones = tk.Frame(barra, bg=T.SURFACE)
        botones.pack(side="right")
        if session.es_admin():
            Button(botones, "Eliminar", self._eliminar, "danger", small=True).pack(side="right", padx=(6, 0))
        Button(botones, "Historial", self._historial, "accent", small=True).pack(side="right", padx=(6, 0))
        Button(botones, "Editar", self._editar, "outline", small=True).pack(side="right")

        self.tabla = DataTable(card.body, [
            ("tipo", "Doc.", 80, "center"), ("num", "Número", 110, "w"), ("nombres", "Nombres", 150, "w"),
            ("apellidos", "Apellidos", 190, "w"), ("tel", "Teléfono", 110, "center"),
            ("email", "Correo", 230, "w"), ("viajes", "Viajes", 70, "center"),
            ("registro", "Registrado", 130, "center")], height=16, on_double=lambda p: self._editar())
        self.tabla.pack(fill="both", expand=True)
        self._cargar()
        e.focus_set()

    def _cargar(self):
        filas = ventas.listar_pasajeros(self.var_buscar.get())
        self.tabla.set_rows(filas, lambda p: (p["tipo_doc"], p["num_doc"], p["nombres"], p["apellidos"],
                                              p["telefono"] or "—", p["email"] or "—", p["viajes"],
                                              utils.fecha_hora(p["creado_en"])[:10]),
                            tag=lambda p: "ok" if p["viajes"] >= 5 else None, vacio="Sin resultados")
        self.lbl_total.configure(text=f"{len(filas)} pasajeros")

    def _seleccionado(self):
        p = self.tabla.selected()
        if not p:
            self.info("Selecciona un pasajero de la tabla.", "Atención")
        return p

    def _nuevo(self):
        d = FormDialog(self, "Nuevo pasajero", CAMPOS, on_submit=ventas.guardar_pasajero)
        self.wait_window(d)
        if d.result:
            self._cargar()

    def _editar(self):
        p = self._seleccionado()
        if not p:
            return
        d = FormDialog(self, "Editar pasajero", CAMPOS, initial=p,
                       on_submit=lambda data: ventas.guardar_pasajero(data, p["id"]))
        self.wait_window(d)
        if d.result:
            self._cargar()

    def _eliminar(self):
        p = self._seleccionado()
        if not p or not self.confirmar(f"¿Eliminar a {p['nombre_completo']}?"):
            return
        try:
            ventas.eliminar_pasajero(p["id"])
        except AppError as e:
            return self.error(e)
        self._cargar()

    def _historial(self):
        p = self._seleccionado()
        if not p:
            return
        win = tk.Toplevel(self)
        win.withdraw()
        win.title(f"Historial · {p['nombre_completo']}")
        win.configure(bg=T.BG)
        head = tk.Frame(win, bg=T.PRIMARY)
        head.pack(fill="x")
        tk.Label(head, text=p["nombre_completo"], bg=T.PRIMARY, fg="#fff", font=T.font(14, "bold")).pack(
            anchor="w", padx=20, pady=(14, 0))
        tk.Label(head, text=f"{p['tipo_doc']} {p['num_doc']} · {p['viajes']} viajes", bg=T.PRIMARY,
                 fg="#cfe0ff", font=T.font(9)).pack(anchor="w", padx=20, pady=(0, 12))
        filas = ventas.historial_pasajero(p["id"])
        t = DataTable(win, [("fecha", "Fecha", 110, "center"), ("hora", "Hora", 60, "center"),
                            ("ruta", "Ruta", 160, "w"), ("asiento", "Asiento", 70, "center"),
                            ("precio", "Precio", 90, "e"), ("estado", "Estado", 100, "center"),
                            ("codigo", "Boleto", 150, "w")], height=10)
        t.pack(fill="both", expand=True, padx=16, pady=16)
        t.set_rows(filas, lambda b: (utils.fecha_corta(b["fecha"]), b["hora_salida"], b["ruta"], b["asiento"],
                                     utils.dinero(b["precio"]), b["estado"].capitalize(), b["codigo"]),
                   tag=lambda b: {"anulado": "muted", "reservado": "warn"}.get(b["estado"]),
                   vacio="Este pasajero aún no tiene viajes")
        total = sum(b["precio"] for b in filas if b["estado"] == "vendido")
        tk.Label(win, text=f"Total gastado: {utils.dinero(total)}", bg=T.BG, fg=T.TEXT,
                 font=T.font(11, "bold")).pack(anchor="e", padx=18, pady=(0, 14))
        win.deiconify()
        modal(win, self)
