"""Rutas, horarios y viajes programados."""
import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk

from ... import config, session, utils
from ...errors import AppError
from ...services import catalogos, viajes
from .. import theme as T
from ..shell import View
from ..widgets import Button, Card, DataTable, FormDialog, combo, etiqueta_estado, label
from .comun import etiqueta_fecha


def duracion(minutos):
    return f"{minutos // 60}h {minutos % 60:02d}m"


class RutasView(View):
    titulo = "RUTAS Y HORARIOS"
    subtitulo = "Destinos, horarios fijos de salida y viajes programados"

    def build(self):
        self.admin = session.es_admin()
        nb = ttk.Notebook(self.cuerpo)
        nb.pack(fill="both", expand=True)
        t1 = tk.Frame(nb, bg=T.BG)
        t2 = tk.Frame(nb, bg=T.BG)
        nb.add(t1, text="  Rutas y horarios  ")
        nb.add(t2, text="  Viajes programados  ")
        self._tab_rutas(t1)
        self._tab_viajes(t2)
        if not self.admin:
            self.lbl_sub.configure(text=self.subtitulo + "   ·   (solo lectura)")

    # ================================================================ rutas
    def _tab_rutas(self, tab):
        tab.columnconfigure(0, weight=3, uniform="r")
        tab.columnconfigure(1, weight=2, uniform="r")
        tab.rowconfigure(0, weight=1)

        card = Card(tab, "RUTAS")
        card.grid(row=0, column=0, sticky="nsew", pady=(14, 0))
        if self.admin:
            Button(card.actions, "Eliminar", self._eliminar_ruta, "danger", small=True).pack(side="right", padx=(6, 0))
            Button(card.actions, "Editar", self._editar_ruta, "outline", small=True).pack(side="right", padx=(6, 0))
            Button(card.actions, "+ Nueva", self._nueva_ruta, "primary", small=True).pack(side="right")
        self.t_rutas = DataTable(card.body, [
            ("codigo", "Código", 70, "center"), ("ruta", "Ruta", 180, "w"), ("km", "Km", 70, "center"),
            ("dur", "Duración", 90, "center"), ("precio", "Precio", 90, "e"),
            ("horarios", "Salidas/día", 90, "center")], height=14, on_select=self._cargar_horarios)
        self.t_rutas.pack(fill="both", expand=True)

        self.card_h = Card(tab, "HORARIOS")
        self.card_h.grid(row=0, column=1, sticky="nsew", padx=(16, 0), pady=(14, 0))
        if self.admin:
            Button(self.card_h.actions, "Eliminar", self._eliminar_horario, "danger", small=True).pack(
                side="right", padx=(6, 0))
            Button(self.card_h.actions, "+ Horario", self._nuevo_horario, "primary", small=True).pack(side="right")
        self.t_horarios = DataTable(self.card_h.body, [("hora", "Hora", 70, "center"), ("bus", "Bus", 70, "center"),
                                                       ("conductor", "Conductor", 180, "w")], height=14)
        self.t_horarios.pack(fill="both", expand=True)
        label(self.card_h.body, "Los horarios se usan para generar los viajes de los próximos días.",
              weight="normal", wraplength=320, justify="left").pack(anchor="w", pady=(8, 0))
        self._cargar_rutas()

    def _cargar_rutas(self, seleccionar=None):
        rutas = catalogos.listar_rutas()
        self.t_rutas.set_rows(rutas, lambda r: (r["codigo"], r["nombre"], f"{r['distancia_km']:.0f}",
                                                duracion(r["duracion_min"]), utils.dinero(r["precio_base"]),
                                                r["num_horarios"]))
        if rutas:
            self.t_rutas.select(seleccionar or rutas[0]["id"])

    def _cargar_horarios(self, ruta=None):
        ruta = ruta or self.t_rutas.selected()
        if not ruta:
            return
        self.card_h.set_title(f"HORARIOS · {ruta['nombre'].upper()}")
        self.t_horarios.set_rows(catalogos.listar_horarios(ruta["id"]),
                                 lambda h: (h["hora"], h["unidad"], h["conductor"]),
                                 vacio="Sin horarios")

    def _campos_ruta(self):
        return [{"key": "codigo", "label": "Código", "required": True},
                {"key": "precio_base", "label": "Precio base (S/)", "required": True},
                {"key": "origen", "label": "Origen", "required": True, "default": "Lima"},
                {"key": "destino", "label": "Destino", "required": True},
                {"key": "distancia_km", "label": "Distancia (km)", "required": True},
                {"key": "duracion_min", "label": "Duración (minutos)", "required": True}]

    def _nueva_ruta(self):
        d = FormDialog(self, "Nueva ruta", self._campos_ruta(), on_submit=catalogos.guardar_ruta)
        self.wait_window(d)
        if d.result:
            self._cargar_rutas()

    def _editar_ruta(self):
        r = self.t_rutas.selected()
        if not r:
            return self.info("Selecciona una ruta.", "Atención")
        d = FormDialog(self, f"Editar ruta {r['codigo']}", self._campos_ruta(), initial=r,
                       on_submit=lambda data: catalogos.guardar_ruta(data, r["id"]))
        self.wait_window(d)
        if d.result:
            self._cargar_rutas(r["id"])

    def _eliminar_ruta(self):
        r = self.t_rutas.selected()
        if not r or not self.confirmar(f"¿Eliminar la ruta {r['nombre']}?\nTambién se eliminarán sus horarios."):
            return
        try:
            catalogos.eliminar_ruta(r["id"])
        except AppError as e:
            return self.error(e)
        self._cargar_rutas()

    def _opciones(self):
        buses = [(b["id"], f"{b['unidad']} · {b['placa']} ({b['capacidad']} asientos)")
                 for b in catalogos.listar_buses(solo_operativos=True)]
        conductores = [(c["id"], c["nombre_completo"]) for c in catalogos.listar_conductores(solo_activos=True)]
        return buses, conductores

    def _nuevo_horario(self):
        r = self.t_rutas.selected()
        if not r:
            return self.info("Selecciona una ruta.", "Atención")
        buses, conductores = self._opciones()
        campos = [{"key": "hora", "label": "Hora de salida (HH:MM)", "required": True},
                  {"key": "bus_id", "label": "Bus", "type": "combo", "options": buses, "required": True},
                  {"key": "conductor_id", "label": "Conductor", "type": "combo", "options": conductores,
                   "required": True}]

        def guardar(data):
            data["ruta_id"] = r["id"]
            catalogos.guardar_horario(data)

        d = FormDialog(self, f"Nuevo horario · {r['nombre']}", campos, on_submit=guardar)
        self.wait_window(d)
        if d.result:
            viajes.programar_desde_horarios(config.DIAS_A_PROGRAMAR)
            self._cargar_rutas(r["id"])
            self._cargar_viajes()

    def _eliminar_horario(self):
        h = self.t_horarios.selected()
        if not h or not self.confirmar(f"¿Eliminar el horario de las {h['hora']}?\n"
                                       "Los viajes ya programados se mantienen."):
            return
        try:
            catalogos.eliminar_horario(h["id"])
        except AppError as e:
            return self.error(e)
        self._cargar_rutas(h["ruta_id"])

    # ================================================================ viajes
    def _tab_viajes(self, tab):
        card = Card(tab, "VIAJES")
        card.pack(fill="both", expand=True, pady=(14, 0))
        if self.admin:
            Button(card.actions, "Cancelar viaje", self._cancelar, "danger", small=True).pack(side="right", padx=(6, 0))
            Button(card.actions, "Generar desde horarios", self._generar, "accent", small=True).pack(
                side="right", padx=(6, 0))
            Button(card.actions, "+ Programar viaje", self._programar, "primary", small=True).pack(side="right")
        fila = tk.Frame(card.body, bg=T.SURFACE)
        fila.pack(fill="x", pady=(0, 10))
        label(fila, "Mostrar").pack(side="left", padx=(0, 8))
        hoy = date.today()
        self._fechas = {"Todos los próximos": None}
        for i in range(-3, 7):
            f = (hoy + timedelta(days=i)).isoformat()
            self._fechas[etiqueta_fecha(f)] = f
        self.var_f = tk.StringVar(value="Todos los próximos")
        cb = combo(fila, self.var_f, list(self._fechas), width=24)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self._cargar_viajes())
        self.t_viajes = DataTable(card.body, [
            ("fecha", "Fecha", 100, "center"), ("hora", "Hora", 60, "center"), ("ruta", "Ruta", 160, "w"),
            ("bus", "Bus", 60, "center"), ("conductor", "Conductor", 190, "w"), ("precio", "Precio", 90, "e"),
            ("vendidos", "Vendidos", 80, "center"), ("libres", "Libres", 70, "center"),
            ("estado", "Estado", 110, "center")], height=15)
        self.t_viajes.pack(fill="both", expand=True)
        self._cargar_viajes()

    def _cargar_viajes(self):
        viajes.actualizar_estados()
        f = self._fechas.get(self.var_f.get())
        lista = viajes.listar(fecha=f) if f else viajes.listar(desde=date.today().isoformat())
        self.t_viajes.set_rows(lista, lambda v: (utils.fecha_corta(v["fecha"]), v["hora_salida"], v["ruta"],
                                                 v["unidad"], v["conductor"], utils.dinero(v["precio"]),
                                                 v["vendidos"], v["libres"], etiqueta_estado(v["estado"])),
                               tag=lambda v: {"cancelado": "bad", "finalizado": "muted",
                                              "en_ruta": "ok"}.get(v["estado"]))

    def _programar(self):
        rutas = [(r["id"], r["nombre"]) for r in catalogos.listar_rutas(solo_activas=True)]
        buses, conductores = self._opciones()
        manana = (date.today() + timedelta(days=1)).isoformat()
        campos = [{"key": "ruta_id", "label": "Ruta", "type": "combo", "options": rutas, "required": True},
                  {"key": "precio", "label": "Precio (S/)", "required": True},
                  {"key": "fecha", "label": "Fecha (AAAA-MM-DD)", "required": True, "default": manana},
                  {"key": "hora_salida", "label": "Hora (HH:MM)", "required": True},
                  {"key": "bus_id", "label": "Bus", "type": "combo", "options": buses, "required": True},
                  {"key": "conductor_id", "label": "Conductor", "type": "combo", "options": conductores,
                   "required": True}]
        d = FormDialog(self, "Programar viaje extra", campos, on_submit=viajes.crear_manual)
        self.wait_window(d)
        if d.result:
            self._cargar_viajes()

    def _generar(self):
        n = viajes.programar_desde_horarios(config.DIAS_A_PROGRAMAR)
        self.info(f"Se generaron {n} viajes nuevos para los próximos {config.DIAS_A_PROGRAMAR} días."
                  if n else "Todos los viajes de los próximos días ya estaban programados.")
        self._cargar_viajes()

    def _cancelar(self):
        v = self.t_viajes.selected()
        if not v:
            return self.info("Selecciona un viaje.", "Atención")
        ocupados = v["vendidos"] + v["reservados"]
        if not self.confirmar(f"¿Cancelar el viaje {v['ruta']} del {v['fecha']} a las {v['hora_salida']}?\n\n"
                              f"Se anularán {ocupados} boletos."):
            return
        try:
            viajes.cancelar(v["id"])
        except AppError as e:
            return self.error(e)
        self._cargar_viajes()
