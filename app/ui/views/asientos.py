"""Mapa de asientos: consulta, confirmación de reservas y anulaciones."""
import tkinter as tk

from ... import session, utils
from ...errors import AppError
from ...services import ventas, viajes
from .. import theme as T
from ..shell import View
from ..ticket import TicketDialog
from ..widgets import Badge, Button, Card, Legend, ProgressBar, SeatMap, label
from .comun import ViajesPanel


class AsientosView(View):
    titulo = "MAPA DE ASIENTOS"
    subtitulo = "Consulta la ocupación de cada unidad, confirma reservas o anula boletos"

    def build(self, viaje_id=None):
        self.viaje, self.asiento = None, None
        c = self.cuerpo
        c.columnconfigure(0, minsize=350)
        c.columnconfigure(1, weight=1)
        c.columnconfigure(2, minsize=370)
        c.rowconfigure(0, weight=1)

        self.panel = ViajesPanel(c, self._seleccionar_viaje, "VIAJES", dias_atras=3)
        self.panel.grid(row=0, column=0, sticky="nsew")

        self.card_mapa = Card(c, "UNIDAD")
        self.card_mapa.grid(row=0, column=1, sticky="nsew", padx=16)
        self.mapa = SeatMap(self.card_mapa.body, "inspect", on_select=self._seleccionar_asiento)
        self.mapa.pack(fill="both", expand=True)
        Legend(self.card_mapa.body, vertical=False, seleccion=False).pack(pady=(10, 0))

        self.card_det = Card(c, "DETALLE")
        self.card_det.grid(row=0, column=2, sticky="nsew")
        d = self.card_det.body
        self.lbl_ruta = tk.Label(d, text="Selecciona un viaje", bg=T.SURFACE, fg=T.TEXT, font=T.font(15, "bold"),
                                 anchor="w")
        self.lbl_ruta.pack(fill="x")
        self.lbl_meta = label(d, "", weight="normal", justify="left", anchor="w")
        self.lbl_meta.pack(fill="x", pady=(2, 8))
        self.barra = ProgressBar(d, height=10)
        self.barra.pack(fill="x")
        self.contadores = tk.Frame(d, bg=T.SURFACE)
        self.contadores.pack(fill="x", pady=(8, 0))
        tk.Frame(d, bg=T.BORDER, height=1).pack(fill="x", pady=14)
        self.det = tk.Frame(d, bg=T.SURFACE)
        self.det.pack(fill="both", expand=True)

        if viaje_id:
            v = viajes.obtener(viaje_id)
            if v:
                self.panel.set_fecha(v["fecha"], viaje_id)

    # ------------------------------------------------------------------ viaje
    def _seleccionar_viaje(self, v):
        self.viaje = viajes.obtener(v["id"])
        v = self.viaje
        self.card_mapa.set_title(f"UNIDAD {v['unidad']} · {v['placa']}")
        self.mapa.load(v["capacidad"], viajes.ocupacion(v["id"]))
        self.lbl_ruta.configure(text=v["ruta"])
        self.lbl_meta.configure(text=f"{utils.fecha_corta(v['fecha'])} · Salida {v['hora_salida']} · "
                                     f"{utils.dinero(v['precio'])}\nConductor: {v['conductor']}")
        self.barra.set((v["vendidos"] + v["reservados"]) / v["capacidad"])
        for w in self.contadores.winfo_children():
            w.destroy()
        for texto, valor, color in (("Vendidos", v["vendidos"], T.SEAT_SOLD),
                                    ("Reservados", v["reservados"], T.SEAT_RESERVED),
                                    ("Libres", v["libres"], T.SEAT_FREE)):
            f = tk.Frame(self.contadores, bg=T.SURFACE)
            f.pack(side="left", expand=True, fill="x")
            tk.Label(f, text=str(valor), bg=T.SURFACE, fg=color, font=T.font(16, "bold")).pack()
            label(f, texto, weight="normal").pack()
        self.asiento = None
        self._limpiar_detalle("Haz clic en un asiento para ver su detalle.")

    def _limpiar_detalle(self, texto=""):
        for w in self.det.winfo_children():
            w.destroy()
        if texto:
            label(self.det, texto, weight="normal").pack(anchor="w")

    # ------------------------------------------------------------------ asiento
    def _seleccionar_asiento(self, n):
        self.asiento = n
        self._limpiar_detalle()
        v = self.viaje
        b = viajes.ocupacion(v["id"]).get(n)
        cab = tk.Frame(self.det, bg=T.SURFACE)
        cab.pack(fill="x")
        tk.Label(cab, text=f"Asiento {n}", bg=T.SURFACE, fg=T.TEXT, font=T.font(14, "bold")).pack(side="left")
        label(cab, f"  {utils.posicion_asiento(n)}", weight="normal").pack(side="left")
        Badge(cab, b["estado"] if b else "libre").pack(side="right")

        programado = v["estado"] == "programado"
        if not b:
            label(self.det, "Este asiento está disponible.", weight="normal").pack(anchor="w", pady=(12, 12))
            if programado:
                Button(self.det, f"Vender asiento {n}",
                       lambda: self.shell.show("venta", viaje_id=v["id"], asiento=n), "orange").pack(fill="x")
            return

        grid = tk.Frame(self.det, bg=T.SURFACE)
        grid.pack(fill="x", pady=(10, 12))
        datos = [("Pasajero", b["pasajero"]), ("Documento", f"{b['tipo_doc']} {b['num_doc']}"),
                 ("Teléfono", b["telefono"] or "—"), ("Boleto", b["codigo"]),
                 ("Pago", f"{b['metodo_pago'].capitalize()} · {utils.dinero(b['precio'])}"),
                 ("Atendido por", b["vendedor"]), ("Emitido", utils.fecha_hora(b["fecha_emision"]))]
        for i, (k, val) in enumerate(datos):
            label(grid, k.upper(), size=8).grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(grid, text=val, bg=T.SURFACE, fg=T.TEXT, font=T.font(10, "bold")).grid(
                row=i, column=1, sticky="w", padx=(14, 0), pady=3)

        Button(self.det, "Ver boleto", lambda: TicketDialog(self, ventas.detalle_boleto(b["id"])),
               "primary").pack(fill="x")
        if programado and b["estado"] == "reservado":
            Button(self.det, "Confirmar pago", lambda: self._confirmar(b), "success").pack(fill="x", pady=(8, 0))
        if programado and (b["estado"] == "reservado" or session.es_admin()):
            Button(self.det, "Anular boleto", lambda: self._anular(b), "danger").pack(fill="x", pady=(8, 0))
        elif programado:
            label(self.det, "Solo el administrador puede anular boletos pagados.", weight="normal").pack(
                anchor="w", pady=(10, 0))

    def _confirmar(self, b):
        try:
            nuevo = ventas.confirmar_reserva(b["id"])
        except AppError as e:
            return self.error(e)
        self._refrescar()
        TicketDialog(self, nuevo)

    def _anular(self, b):
        if not self.confirmar(f"¿Anular el boleto {b['codigo']} del asiento {b['asiento']}?\n"
                              f"El asiento quedará libre."):
            return
        try:
            ventas.anular_boleto(b["id"])
        except AppError as e:
            return self.error(e)
        self._refrescar()

    def _refrescar(self):
        asiento = self.asiento
        self.panel.reload(seleccionar=self.viaje["id"])
        self._seleccionar_viaje(self.viaje)
        self.mapa.selected = asiento
        self.mapa.redraw()
        self._seleccionar_asiento(asiento)
        self.shell.topbar.actualizar_badge()
