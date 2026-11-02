"""Tablero principal."""
import tkinter as tk
from datetime import date

from ... import utils
from ...services import configuracion, informes, viajes, ventas
from .. import theme as T
from ..shell import View
from ..widgets import (Button, Card, DataTable, Legend, ProgressBar, SeatMap, StatCard,
                       combo, label)


class DashboardView(View):
    titulo = "TABLERO PRINCIPAL"

    def build(self):
        viajes.actualizar_estados()
        empresa = configuracion.obtener("empresa_nombre")
        self.set_titulo(f"TABLERO PRINCIPAL - [{empresa}]",
                        f"Resumen de operaciones · {utils.fecha_larga()}")
        Button(self.acciones, "+  Nueva venta", lambda: self.shell.show("venta"), "orange").pack(side="right")
        Button(self.acciones, "Actualizar", lambda: self.shell.show("dashboard"), "ghost").pack(
            side="right", padx=8)

        # -------- indicadores
        k = informes.kpis_hoy()
        fila = tk.Frame(self.cuerpo, bg=T.BG)
        fila.pack(fill="x")
        tarjetas = [
            ("Viajes de hoy", f"{k['viajes']} viajes", "suitcase", T.ACCENT, f"{k['por_salir']} por salir"),
            ("Pasajeros registrados", f"{k['pasajeros']}", "person_plus", T.SUCCESS,
             f"+{k['pasajeros_nuevos']} nuevos hoy"),
            ("Ventas hoy", utils.dinero(k["ventas_hoy"]), "money", T.ORANGE, f"{k['boletos_hoy']} boletos vendidos"),
            ("Ocupación hoy", f"{k['ocupacion']:.0f}%", "chart", T.PRIMARY,
             f"{k['asientos_ocupados']} de {k['asientos_total']} asientos"),
        ]
        for i, (t, v, ic, c, s) in enumerate(tarjetas):
            fila.columnconfigure(i, weight=1, uniform="kpi")
            StatCard(fila, t, v, ic, c, s).grid(row=0, column=i, sticky="nsew",
                                                 padx=(0 if i == 0 else 8, 0 if i == 3 else 8))

        # -------- zona inferior
        abajo = tk.Frame(self.cuerpo, bg=T.BG)
        abajo.pack(fill="both", expand=True, pady=(16, 0))
        abajo.columnconfigure(0, weight=5, uniform="dash")
        abajo.columnconfigure(1, weight=6, uniform="dash")
        abajo.rowconfigure(0, weight=1)

        self._construir_mapa(abajo)
        der = tk.Frame(abajo, bg=T.BG)
        der.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        self._construir_salidas(der)
        self._construir_ultimas(der)

    # ------------------------------------------------------------------ mapa
    def _construir_mapa(self, parent):
        self.card_mapa = Card(parent, "MAPA DE UNIDAD")
        self.card_mapa.grid(row=0, column=0, sticky="nsew")
        body = self.card_mapa.body

        hoy = [v for v in viajes.de_hoy() if v["estado"] != "cancelado"]
        self._opciones = {f"{v['hora_salida']} · {v['ruta']} · Unidad {v['unidad']}": v for v in hoy}
        self.var_viaje = tk.StringVar()
        cb = combo(body, self.var_viaje, list(self._opciones), width=40)
        cb.pack(fill="x", pady=(0, 8))
        cb.bind("<<ComboboxSelected>>", lambda e: self._cargar(self._opciones[self.var_viaje.get()]))

        cont = tk.Frame(body, bg=T.SURFACE)
        cont.pack(fill="both", expand=True)
        self.mapa = SeatMap(cont, mode="sell", on_select=self._asiento, on_info=self._info_asiento)
        self.mapa.pack(side="left", fill="both", expand=True)

        lado = tk.Frame(cont, bg=T.SURFACE, width=170)
        lado.pack(side="right", fill="y", padx=(10, 0))
        lado.pack_propagate(False)
        label(lado, "ESTATUS", fg=T.TEXT, size=10).pack(anchor="w", pady=(4, 6))
        Legend(lado).pack(anchor="w")
        tk.Frame(lado, bg=T.BORDER, height=1).pack(fill="x", pady=12)
        self.lbl_info = tk.Label(lado, text="", bg=T.SURFACE, fg=T.TEXT, font=T.font(9),
                                 justify="left", wraplength=165)
        self.lbl_info.pack(anchor="w")
        self.barra = ProgressBar(lado, height=8)
        self.barra.pack(fill="x", pady=(8, 2))
        self.lbl_ocup = label(lado, "", weight="normal")
        self.lbl_ocup.pack(anchor="w")
        self.btn_vender = Button(lado, "Vender", self._vender, "orange", small=True)
        self.btn_vender.pack(side="bottom", fill="x", pady=(8, 0))

        v = viajes.proximo_de_hoy()
        if v and v["fecha"] == date.today().isoformat():
            for texto, op in self._opciones.items():
                if op["id"] == v["id"]:
                    self.var_viaje.set(texto)
            self._cargar(v)
        elif v:
            self._cargar(v)
        else:
            self.mapa.clear("No hay viajes programados")

    def _cargar(self, viaje):
        self.viaje = viajes.obtener(viaje["id"])
        v = self.viaje
        self.card_mapa.set_title(f"MAPA DE UNIDAD {v['unidad']}")
        self.mapa.load(v["capacidad"], viajes.ocupacion(v["id"]))
        self.lbl_info.configure(text=f"{v['ruta']}\n{utils.fecha_corta(v['fecha'])} · {v['hora_salida']}\n"
                                     f"Conductor: {v['conductor']}\nPrecio: {utils.dinero(v['precio'])}")
        ocupados = v["vendidos"] + v["reservados"]
        self.barra.set(ocupados / v["capacidad"] if v["capacidad"] else 0)
        self.lbl_ocup.configure(text=f"{ocupados}/{v['capacidad']} ocupados · {v['libres']} libres")
        self.btn_vender.set_enabled(v["estado"] == "programado" and v["libres"] > 0)
        self.btn_vender.configure(text="Vender en este viaje")

    def _asiento(self, n):
        if n:
            self.btn_vender.configure(text=f"Vender asiento {n}")
        else:
            self.btn_vender.configure(text="Vender en este viaje")

    def _info_asiento(self, n, boleto):
        self.info(f"Asiento {n} ({utils.posicion_asiento(n)})\n\n"
                  f"Pasajero: {boleto['pasajero']}\nDocumento: {boleto['tipo_doc']} {boleto['num_doc']}\n"
                  f"Estado: {boleto['estado'].capitalize()}\nBoleto: {boleto['codigo']}",
                  "Asiento ocupado")

    def _vender(self):
        if getattr(self, "viaje", None):
            self.shell.show("venta", viaje_id=self.viaje["id"], asiento=self.mapa.selected)

    # ------------------------------------------------------------------ salidas
    def _construir_salidas(self, parent):
        card = Card(parent, "RESUMEN DE RUTAS · PRÓXIMAS SALIDAS")
        card.pack(fill="x")
        tabla = tk.Frame(card.body, bg=T.SURFACE)
        tabla.pack(fill="x")
        cabeceras = ["Ruta", "Salida", "Bus", "Libres", ""]
        for c, texto in enumerate(cabeceras):
            tk.Label(tabla, text=texto, bg="#f2f6fb", fg=T.MUTED, font=T.font(9, "bold"),
                     anchor="w", padx=8, pady=7).grid(row=0, column=c, sticky="ew")
        tabla.columnconfigure(0, weight=1)

        hoy = date.today().isoformat()
        proximos = viajes.listar(desde=hoy, solo_vendibles=True)[:6]
        if not proximos:
            label(tabla, "No hay salidas programadas", weight="normal").grid(row=1, column=0, columnspan=5, pady=12)
        for r, v in enumerate(proximos, start=1):
            bg = T.SURFACE if r % 2 else T.SURFACE_ALT
            hora = v["hora_salida"] if v["fecha"] == hoy else f"{v['fecha'][8:10]}/{v['fecha'][5:7]} {v['hora_salida']}"
            color_libres = T.DANGER if v["libres"] == 0 else (T.ORANGE if v["libres"] <= 5 else T.TEXT)
            valores = [(v["ruta"], T.TEXT), (hora, T.TEXT), (v["unidad"], T.TEXT),
                       ("Lleno" if v["libres"] == 0 else str(v["libres"]), color_libres)]
            for c, (texto, fg) in enumerate(valores):
                tk.Label(tabla, text=texto, bg=bg, fg=fg, font=T.font(10, "bold" if c == 3 else "normal"),
                         anchor="w" if c == 0 else "center", padx=8, pady=8).grid(row=r, column=c, sticky="nsew")
            botones = tk.Frame(tabla, bg=bg)
            botones.grid(row=r, column=4, sticky="nsew", padx=(4, 8))
            Button(botones, "Ver detalles", lambda vid=v["id"]: self.shell.show("asientos", viaje_id=vid),
                   "primary", small=True).pack(side="left", pady=5)
            b = Button(botones, "Vender", lambda vid=v["id"]: self.shell.show("venta", viaje_id=vid),
                       "orange", small=True)
            b.pack(side="left", padx=(6, 0), pady=5)
            b.set_enabled(v["libres"] > 0)

    def _construir_ultimas(self, parent):
        card = Card(parent, "ÚLTIMAS VENTAS")
        card.pack(fill="both", expand=True, pady=(16, 0))
        t = DataTable(card.body, [("hora", "Hora", 60, "center"), ("pasajero", "Pasajero", 170, "w"),
                                  ("ruta", "Ruta", 130, "w"), ("asiento", "Asiento", 60, "center"),
                                  ("monto", "Monto", 80, "e")], height=4)
        t.pack(fill="both", expand=True)
        t.set_rows(ventas.ultimas_ventas(10),
                   lambda b: (b["fecha_emision"][11:16], b["pasajero"], b["ruta"], b["asiento"], utils.dinero(b["precio"])),
                   tag=lambda b: "warn" if b["estado"] == "reservado" else None)
