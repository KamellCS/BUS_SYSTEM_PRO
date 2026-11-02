"""Venta de pasajes: viaje → asiento → pasajero → boleto."""
import tkinter as tk

from ... import config, utils
from ...errors import AppError
from ...services import ventas, viajes
from .. import theme as T
from ..shell import View
from ..ticket import TicketDialog
from ..widgets import Button, Card, Legend, SeatMap, combo, entry, label
from .comun import ViajesPanel


class VentaView(View):
    titulo = "VENTA DE PASAJES"
    subtitulo = "1) Elige el viaje   ·   2) Selecciona el asiento   ·   3) Registra al pasajero y cobra"

    def build(self, viaje_id=None, asiento=None):
        self.viaje, self.asiento, self._asiento_inicial = None, None, asiento
        c = self.cuerpo
        c.columnconfigure(0, minsize=350)
        c.columnconfigure(1, weight=1)
        c.columnconfigure(2, minsize=390)
        c.rowconfigure(0, weight=1)

        self.panel = ViajesPanel(c, self._seleccionar_viaje, "1. ELIGE EL VIAJE", solo_vendibles=True)
        self.panel.grid(row=0, column=0, sticky="nsew")

        self.card_mapa = Card(c, "2. ELIGE EL ASIENTO")
        self.card_mapa.grid(row=0, column=1, sticky="nsew", padx=16)
        self.mapa = SeatMap(self.card_mapa.body, "sell", on_select=self._seleccionar_asiento,
                            on_info=self._info_ocupado)
        self.mapa.pack(fill="both", expand=True)
        Legend(self.card_mapa.body, vertical=False).pack(pady=(10, 0))

        card = Card(c, "3. PASAJERO Y PAGO")
        card.grid(row=0, column=2, sticky="nsew")
        self._formulario(card.body)

        if viaje_id:
            v = viajes.obtener(viaje_id)
            if v:
                self.panel.set_fecha(v["fecha"], viaje_id)

    # ------------------------------------------------------------------ formulario
    def _formulario(self, f):
        f.columnconfigure(0, weight=1, uniform="f")
        f.columnconfigure(1, weight=1, uniform="f")
        self.v = {k: tk.StringVar() for k in ("tipo_doc", "num_doc", "nombres", "apellidos",
                                               "telefono", "email", "metodo")}
        self.v["tipo_doc"].set("DNI")
        self.v["metodo"].set("efectivo")

        label(f, "Tipo de documento").grid(row=0, column=0, sticky="w", pady=(0, 3))
        label(f, "Número de documento  *").grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 3))
        combo(f, self.v["tipo_doc"], config.TIPOS_DOC, width=12).grid(row=1, column=0, sticky="ew")
        doc = entry(f, self.v["num_doc"], width=14)
        doc.grid(row=1, column=1, sticky="ew", padx=(10, 0), ipady=6)
        doc.bind("<Return>", lambda e: self._buscar())
        doc.bind("<FocusOut>", lambda e: self._buscar())
        self.lbl_cliente = label(f, "Escribe el documento y presiona Enter para buscar", weight="normal")
        self.lbl_cliente.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))

        filas = [("Nombres  *", "nombres", "Apellidos  *", "apellidos"),
                 ("Teléfono", "telefono", "Correo", "email")]
        r = 3
        for t1, k1, t2, k2 in filas:
            label(f, t1).grid(row=r, column=0, sticky="w", pady=(10, 3))
            label(f, t2).grid(row=r, column=1, sticky="w", padx=(10, 0), pady=(10, 3))
            entry(f, self.v[k1], width=14).grid(row=r + 1, column=0, sticky="ew", ipady=6)
            entry(f, self.v[k2], width=14).grid(row=r + 1, column=1, sticky="ew", padx=(10, 0), ipady=6)
            r += 2
        label(f, "Método de pago").grid(row=r, column=0, sticky="w", pady=(10, 3))
        combo(f, self.v["metodo"], config.METODOS_PAGO, width=12).grid(row=r + 1, column=0, columnspan=2,
                                                                       sticky="ew")

        # resumen
        res = tk.Frame(f, bg=T.ACCENT_SOFT, highlightthickness=1, highlightbackground="#bfe9ef")
        res.grid(row=r + 2, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self.lbl_resumen = tk.Label(res, text="", bg=T.ACCENT_SOFT, fg=T.TEXT, font=T.font(9),
                                    justify="left", anchor="w")
        self.lbl_resumen.pack(side="left", padx=12, pady=10, fill="x", expand=True)
        tot = tk.Frame(res, bg=T.ACCENT_SOFT)
        tot.pack(side="right", padx=12)
        tk.Label(tot, text="TOTAL", bg=T.ACCENT_SOFT, fg=T.ACCENT_DARK, font=T.font(8, "bold")).pack(anchor="e")
        self.lbl_total = tk.Label(tot, text=utils.dinero(0), bg=T.ACCENT_SOFT, fg=T.TEXT, font=T.font(17, "bold"))
        self.lbl_total.pack(anchor="e")

        self.btn_vender = Button(f, "Vender boleto", lambda: self._emitir("vendido"), "success")
        self.btn_vender.grid(row=r + 3, column=0, columnspan=2, sticky="ew", pady=(14, 6))
        Button(f, "Reservar", lambda: self._emitir("reservado"), "warning").grid(row=r + 4, column=0, sticky="ew")
        Button(f, "Limpiar", self._limpiar, "ghost").grid(row=r + 4, column=1, sticky="ew", padx=(10, 0))
        self._actualizar_resumen()

    # ------------------------------------------------------------------ eventos
    def _seleccionar_viaje(self, v):
        self.viaje = viajes.obtener(v["id"])
        self.card_mapa.set_title(f"2. ELIGE EL ASIENTO · UNIDAD {self.viaje['unidad']}")
        ocupados = viajes.ocupacion(v["id"])
        inicial = self._asiento_inicial if self._asiento_inicial and self._asiento_inicial not in ocupados else None
        self._asiento_inicial = None
        self.mapa.load(self.viaje["capacidad"], ocupados, selected=inicial)
        self.asiento = inicial
        self._actualizar_resumen()

    def _seleccionar_asiento(self, n):
        self.asiento = n
        self._actualizar_resumen()

    def _info_ocupado(self, n, b):
        self.info(f"El asiento {n} está {b['estado']}.\n\nPasajero: {b['pasajero']}\nBoleto: {b['codigo']}",
                  "Asiento no disponible")

    def _buscar(self):
        try:
            p = ventas.buscar_pasajero(self.v["tipo_doc"].get(), self.v["num_doc"].get())
        except AppError:
            p = None
        if not self.v["num_doc"].get().strip():
            return
        if p:
            for k in ("nombres", "apellidos", "telefono", "email"):
                self.v[k].set(p.get(k) or "")
            self.lbl_cliente.configure(text=f"✔  Pasajero registrado · {p['viajes']} viajes", fg=T.SUCCESS_DARK)
        else:
            self.lbl_cliente.configure(text="Pasajero nuevo: completa sus datos", fg=T.ORANGE_DARK)

    def _actualizar_resumen(self):
        v = self.viaje
        if not v:
            self.lbl_resumen.configure(text="Selecciona un viaje y un asiento")
            self.lbl_total.configure(text=utils.dinero(0))
            return
        asiento = f"{self.asiento} ({utils.posicion_asiento(self.asiento)})" if self.asiento else "—"
        self.lbl_resumen.configure(text=f"{v['ruta']}\n{utils.fecha_corta(v['fecha'])} · {v['hora_salida']}"
                                        f" · Unidad {v['unidad']}\nAsiento: {asiento}")
        self.lbl_total.configure(text=utils.dinero(v["precio"]))

    def _datos(self):
        return {k: self.v[k].get() for k in ("tipo_doc", "num_doc", "nombres", "apellidos", "telefono", "email")}

    def _emitir(self, estado):
        try:
            boleto = ventas.emitir_boleto(self.viaje["id"] if self.viaje else None, self.asiento,
                                          self._datos(), self.v["metodo"].get(), estado)
        except AppError as e:
            self.error(e)
            return
        viaje_id = self.viaje["id"]
        self._limpiar()
        self.panel.reload(seleccionar=viaje_id)
        self._seleccionar_viaje({"id": viaje_id})
        self.shell.topbar.actualizar_badge()
        TicketDialog(self, boleto)

    def _limpiar(self):
        for k in ("num_doc", "nombres", "apellidos", "telefono", "email"):
            self.v[k].set("")
        self.lbl_cliente.configure(text="Escribe el documento y presiona Enter para buscar", fg=T.MUTED)
        self.asiento = None
        self.mapa.selected = None
        self.mapa.redraw()
        self._actualizar_resumen()
