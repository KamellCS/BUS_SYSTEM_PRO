"""Informes de ventas (solo administrador)."""
import tkinter as tk
from datetime import date
from tkinter import filedialog

from ... import utils
from ...errors import AppError
from ...services import informes
from .. import theme as T
from ..shell import View
from ..widgets import BarChart, Button, Card, DataTable, StatCard, combo, label

PERIODOS = {"Hoy": 1, "Últimos 7 días": 7, "Últimos 30 días": 30, "Todo el historial": None}


class InformesView(View):
    titulo = "INFORMES"
    subtitulo = "Ingresos, rutas más vendidas y desempeño del equipo"

    def build(self):
        self.var_p = tk.StringVar(value="Últimos 7 días")
        Button(self.acciones, "Exportar CSV", self._exportar, "success").pack(side="right")
        cb = combo(self.acciones, self.var_p, list(PERIODOS), width=18)
        cb.pack(side="right", padx=10)
        cb.bind("<<ComboboxSelected>>", lambda e: self._cargar())
        label(self.acciones, "Periodo", bg=T.BG).pack(side="right")

        self.kpis = tk.Frame(self.cuerpo, bg=T.BG)
        self.kpis.pack(fill="x")
        self.tarjetas = {}
        for i, (k, t, ic, c) in enumerate((("ingresos", "Ingresos", "money", T.SUCCESS),
                                           ("vendidos", "Boletos vendidos", "ticket", T.PRIMARY),
                                           ("promedio", "Ticket promedio", "chart", T.ACCENT),
                                           ("reservas", "Reservas por cobrar", "seat", T.ORANGE))):
            self.kpis.columnconfigure(i, weight=1, uniform="k")
            sc = StatCard(self.kpis, t, "—", ic, c)
            sc.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0 if i == 3 else 8))
            self.tarjetas[k] = sc

        medio = tk.Frame(self.cuerpo, bg=T.BG)
        medio.pack(fill="both", expand=True, pady=(16, 0))
        medio.columnconfigure(0, weight=3, uniform="m")
        medio.columnconfigure(1, weight=2, uniform="m")
        medio.rowconfigure(0, weight=1)
        medio.rowconfigure(1, weight=1)

        self.card_graf = Card(medio, "INGRESOS POR DÍA")
        self.card_graf.grid(row=0, column=0, sticky="nsew")
        self.grafico = BarChart(self.card_graf.body, height=200)
        self.grafico.pack(fill="both", expand=True)

        c2 = Card(medio, "MÉTODOS DE PAGO")
        c2.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        self.t_metodos = DataTable(c2.body, [("m", "Método", 120, "w"), ("b", "Boletos", 80, "center"),
                                             ("i", "Ingresos", 110, "e"), ("p", "%", 60, "center")], height=5)
        self.t_metodos.pack(fill="both", expand=True)

        c3 = Card(medio, "VENTAS POR RUTA")
        c3.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        self.t_rutas = DataTable(c3.body, [("pos", "#", 40, "center"), ("ruta", "Ruta", 200, "w"),
                                           ("b", "Boletos", 90, "center"), ("i", "Ingresos", 120, "e"),
                                           ("p", "% del total", 100, "center")], height=6)
        self.t_rutas.pack(fill="both", expand=True)

        c4 = Card(medio, "VENTAS POR VENDEDOR")
        c4.grid(row=1, column=1, sticky="nsew", padx=(16, 0), pady=(16, 0))
        self.t_vend = DataTable(c4.body, [("v", "Vendedor", 150, "w"), ("b", "Boletos", 80, "center"),
                                          ("i", "Ingresos", 110, "e")], height=6)
        self.t_vend.pack(fill="both", expand=True)
        self._cargar()

    @property
    def dias(self):
        return PERIODOS[self.var_p.get()]

    def _cargar(self):
        dias = self.dias
        r = informes.resumen(dias)
        self.tarjetas["ingresos"].set(utils.dinero(r["ingresos"]), f"{r['anulados']} boletos anulados")
        self.tarjetas["vendidos"].set(f"{r['vendidos']:,}", self.var_p.get())
        self.tarjetas["promedio"].set(utils.dinero(r["promedio"]), "por boleto")
        self.tarjetas["reservas"].set(str(r["reservas"]), "pendientes de pago")

        n = 14 if dias in (None, 1, 7) else 30
        n = max(n, 7)
        self.card_graf.set_title(f"INGRESOS POR DÍA · ÚLTIMOS {n} DÍAS")
        self.grafico.load(informes.ingresos_por_dia(n))

        total = r["ingresos"] or 1
        rutas = informes.ventas_por_ruta(dias)
        for i, f in enumerate(rutas, 1):
            f["pos"] = i
        self.t_rutas.set_rows(rutas, lambda f: (f["pos"], f["ruta"], f["boletos"], utils.dinero(f["ingresos"]),
                                                f"{f['ingresos'] / total * 100:.1f}%"), key="codigo")
        self.t_vend.set_rows(informes.ventas_por_vendedor(dias),
                             lambda f: (f["vendedor"], f["boletos"], utils.dinero(f["ingresos"])), key="username")
        self.t_metodos.set_rows(informes.ventas_por_metodo(dias),
                                lambda f: (f["metodo_pago"].capitalize(), f["boletos"], utils.dinero(f["ingresos"]),
                                           f"{f['ingresos'] / total * 100:.0f}%"), key="metodo_pago")

    def _exportar(self):
        ruta = filedialog.asksaveasfilename(parent=self, defaultextension=".csv",
                                            initialfile=f"ventas_{date.today():%Y%m%d}.csv",
                                            filetypes=[("CSV (Excel)", "*.csv")])
        if not ruta:
            return
        try:
            n = informes.exportar_csv(ruta, self.dias)
        except (AppError, OSError) as e:
            return self.error(e)
        self.info(f"Se exportaron {n} boletos a:\n{ruta}")
