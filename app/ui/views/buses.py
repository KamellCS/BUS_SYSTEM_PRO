"""Gestión de buses (solo administrador)."""
import tkinter as tk

from ... import config
from ...errors import AppError
from ...services import catalogos
from .. import theme as T
from ..shell import View
from ..widgets import Button, Card, DataTable, FormDialog, StatCard, etiqueta_estado

CAMPOS = [
    {"key": "unidad", "label": "N° de unidad", "required": True},
    {"key": "placa", "label": "Placa (ABC-123)", "required": True},
    {"key": "marca", "label": "Marca", "required": True},
    {"key": "modelo", "label": "Modelo", "required": True},
    {"key": "anio", "label": "Año", "required": True},
    {"key": "capacidad", "label": "Capacidad (asientos)", "required": True, "default": "40"},
    {"key": "estado", "label": "Estado", "type": "combo", "default": "operativo",
     "options": [(e, etiqueta_estado(e)) for e in config.ESTADOS_BUS]},
]


class BusesView(View):
    titulo = "GESTIÓN DE BUSES"
    subtitulo = "Flota de la empresa, capacidad y estado operativo"

    def build(self):
        Button(self.acciones, "+  Nuevo bus", self._nuevo, "primary").pack(side="right")
        self.kpis = tk.Frame(self.cuerpo, bg=T.BG)
        self.kpis.pack(fill="x")
        card = Card(self.cuerpo, "FLOTA")
        card.pack(fill="both", expand=True, pady=(16, 0))
        Button(card.actions, "Eliminar", self._eliminar, "danger", small=True).pack(side="right", padx=(6, 0))
        Button(card.actions, "Cambiar estado", self._estado, "accent", small=True).pack(side="right", padx=(6, 0))
        Button(card.actions, "Editar", self._editar, "outline", small=True).pack(side="right")
        self.tabla = DataTable(card.body, [
            ("unidad", "Unidad", 80, "center"), ("placa", "Placa", 100, "center"), ("marca", "Marca", 150, "w"),
            ("modelo", "Modelo", 160, "w"), ("anio", "Año", 70, "center"), ("cap", "Asientos", 80, "center"),
            ("estado", "Estado", 140, "center"), ("viajes", "Viajes programados", 140, "center")],
            height=14, on_double=lambda b: self._editar())
        self.tabla.pack(fill="both", expand=True)
        self._cargar()

    def _cargar(self):
        buses = catalogos.listar_buses()
        for w in self.kpis.winfo_children():
            w.destroy()
        operativos = [b for b in buses if b["estado"] == "operativo"]
        datos = [("Total de buses", len(buses), "bus", T.PRIMARY),
                 ("Operativos", len(operativos), "check", T.SUCCESS),
                 ("En mantenimiento / fuera", len(buses) - len(operativos), "gear", T.ORANGE),
                 ("Asientos operativos", sum(b["capacidad"] for b in operativos), "seat", T.ACCENT)]
        for i, (t, v, ic, c) in enumerate(datos):
            self.kpis.columnconfigure(i, weight=1, uniform="k")
            StatCard(self.kpis, t, str(v), ic, c).grid(row=0, column=i, sticky="nsew",
                                                        padx=(0 if i == 0 else 8, 0 if i == 3 else 8))
        self.tabla.set_rows(buses, lambda b: (b["unidad"], b["placa"], b["marca"], b["modelo"], b["anio"],
                                              b["capacidad"], etiqueta_estado(b["estado"]),
                                              b["viajes_programados"]),
                            tag=lambda b: {"mantenimiento": "warn", "fuera_servicio": "bad"}.get(b["estado"]))

    def _sel(self):
        b = self.tabla.selected()
        if not b:
            self.info("Selecciona un bus de la tabla.", "Atención")
        return b

    def _nuevo(self):
        d = FormDialog(self, "Nuevo bus", CAMPOS, on_submit=catalogos.guardar_bus)
        self.wait_window(d)
        if d.result:
            self._cargar()

    def _editar(self):
        b = self._sel()
        if not b:
            return
        d = FormDialog(self, f"Editar bus {b['unidad']}", CAMPOS, initial=b,
                       on_submit=lambda data: catalogos.guardar_bus(data, b["id"]))
        self.wait_window(d)
        if d.result:
            self._cargar()

    def _estado(self):
        b = self._sel()
        if not b:
            return
        campos = [{"key": "estado", "label": "Nuevo estado", "type": "combo",
                   "options": [(e, etiqueta_estado(e)) for e in config.ESTADOS_BUS]}]
        d = FormDialog(self, f"Estado del bus {b['unidad']}", campos, initial=b,
                       subtitle="Los buses que no están operativos no reciben viajes nuevos",
                       on_submit=lambda data: catalogos.cambiar_estado_bus(b["id"], data["estado"]))
        self.wait_window(d)
        if d.result:
            self._cargar()

    def _eliminar(self):
        b = self._sel()
        if not b or not self.confirmar(f"¿Eliminar el bus {b['unidad']} ({b['placa']})?"):
            return
        try:
            catalogos.eliminar_bus(b["id"])
        except AppError as e:
            return self.error(e)
        self._cargar()
