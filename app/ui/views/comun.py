"""Piezas compartidas entre vistas."""
import tkinter as tk
from datetime import date, timedelta

from ... import utils
from ...services import viajes
from .. import theme as T
from ..widgets import Card, DataTable, combo, label


def etiqueta_fecha(iso: str) -> str:
    d = date.fromisoformat(iso)
    delta = (d - date.today()).days
    prefijo = {0: "Hoy", 1: "Mañana", -1: "Ayer"}.get(delta)
    return f"{prefijo} · {utils.fecha_corta(iso)}" if prefijo else utils.fecha_corta(iso)


class ViajesPanel(Card):
    """Selector de fecha + tabla de viajes."""

    def __init__(self, parent, on_select, titulo="VIAJES", solo_vendibles=False, dias_atras=0):
        super().__init__(parent, titulo)
        self.on_select_cb = on_select
        self._ultimo = None
        self.solo_vendibles = solo_vendibles
        hoy = date.today()
        self.fechas = [(hoy + timedelta(days=i)).isoformat() for i in range(-dias_atras, 7)]
        self._etiquetas = {etiqueta_fecha(f): f for f in self.fechas}

        fila = tk.Frame(self.body, bg=T.SURFACE)
        fila.pack(fill="x", pady=(0, 10))
        label(fila, "Fecha de viaje").pack(anchor="w")
        self.var_fecha = tk.StringVar(value=etiqueta_fecha(hoy.isoformat()))
        cb = combo(fila, self.var_fecha, list(self._etiquetas), width=30)
        cb.pack(fill="x", pady=(4, 0))
        cb.bind("<<ComboboxSelected>>", lambda e: self.reload())

        self.tabla = DataTable(self.body, [("hora", "Hora", 58, "center"), ("ruta", "Ruta", 150, "w"),
                                           ("bus", "Bus", 52, "center"), ("libres", "Libres", 58, "center")],
                               height=12, on_select=self._seleccion)
        self.tabla.pack(fill="both", expand=True)
        self.resumen = label(self.body, "", fg=T.MUTED, weight="normal")
        self.resumen.pack(anchor="w", pady=(8, 0))
        self.reload()

    @property
    def fecha(self):
        return self._etiquetas.get(self.var_fecha.get(), date.today().isoformat())

    def set_fecha(self, iso, seleccionar=None):
        if iso in self.fechas:
            self.var_fecha.set(etiqueta_fecha(iso))
        self.reload(seleccionar)

    def reload(self, seleccionar=None):
        viajes.actualizar_estados()
        lista = viajes.listar(fecha=self.fecha, solo_vendibles=self.solo_vendibles)
        lista = [v for v in lista if v["estado"] != "cancelado"]

        def tag(v):
            if v["estado"] != "programado":
                return "muted"
            if v["libres"] == 0:
                return "bad"
            return "warn" if v["libres"] <= 5 else None

        def valores(v):
            libres = "Lleno" if v["libres"] == 0 else v["libres"]
            if v["estado"] != "programado":
                libres = Badge_text(v["estado"])
            return (v["hora_salida"], v["ruta"], v["unidad"], libres)

        self.tabla.set_rows(lista, valores, tag=tag,
                            vacio="No hay viajes disponibles" if self.solo_vendibles else "Sin viajes")
        total_libres = sum(v["libres"] for v in lista if v["estado"] == "programado")
        self.resumen.configure(text=f"{len(lista)} viajes · {total_libres} asientos libres")
        ids = {v["id"] for v in lista}
        if seleccionar in ids:
            self.tabla.select(seleccionar)
        elif lista:      # preselecciona la próxima salida disponible
            primero = next((v for v in lista if v["estado"] == "programado"), lista[0])
            self.tabla.select(primero["id"])

    def _seleccion(self, viaje):
        # evita recargar dos veces el mismo viaje (eventos de selección repetidos)
        if viaje and viaje["id"] != self._ultimo:
            self._ultimo = viaje["id"]
            self.on_select_cb(viaje)


def Badge_text(estado):
    return {"en_ruta": "En ruta", "finalizado": "Salió", "cancelado": "Cancelado"}.get(estado, estado)
