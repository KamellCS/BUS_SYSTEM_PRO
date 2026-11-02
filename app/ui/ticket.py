"""Ventana del boleto electrónico."""
import tkinter as tk
from tkinter import filedialog

from .. import utils
from ..services import configuracion
from . import icons, theme as T
from .widgets import Badge, Button, modal


class TicketDialog(tk.Toplevel):
    def __init__(self, parent, boleto: dict):
        super().__init__(parent)
        self.withdraw()
        self.boleto = boleto
        self.title(f"Boleto {boleto['codigo']}")
        self.configure(bg=T.BG)
        self.resizable(False, False)
        empresa = configuracion.obtener("empresa_nombre")

        papel = tk.Frame(self, bg=T.SURFACE, highlightthickness=1, highlightbackground=T.BORDER)
        papel.pack(padx=22, pady=22)

        cab = tk.Canvas(papel, width=420, height=96, highlightthickness=0, bg=T.SIDEBAR_TOP)
        cab.pack()
        icons.gradient(cab, 0, 0, 420, 96, T.SIDEBAR_TOP, T.ACCENT_DARK, step=3, horizontal=True)
        icons.rounded_rect(cab, 20, 22, 72, 74, r=12, fill=T.ACCENT, outline="")
        icons.draw(cab, "bus", 46, 48, 30, "#ffffff", bg=T.ACCENT)
        cab.create_text(86, 38, text="BOLETO ELECTRÓNICO", anchor="w", fill="#ffffff", font=T.font(14, "bold"))
        cab.create_text(86, 62, text=empresa, anchor="w", fill="#cdeff5", font=T.font(10))

        cuerpo = tk.Frame(papel, bg=T.SURFACE)
        cuerpo.pack(fill="x", padx=24, pady=(16, 6))
        top = tk.Frame(cuerpo, bg=T.SURFACE)
        top.pack(fill="x")
        tk.Label(top, text=boleto["codigo"], bg=T.SURFACE, fg=T.MUTED, font=T.font(10, "bold")).pack(side="left")
        Badge(top, boleto["estado"]).pack(side="right")

        tk.Label(cuerpo, text=f"{boleto['origen']}  →  {boleto['destino']}", bg=T.SURFACE, fg=T.TEXT,
                 font=T.font(20, "bold")).pack(anchor="w", pady=(10, 0))
        tk.Label(cuerpo, text=f"{utils.fecha_corta(boleto['fecha'])}  ·  Salida {boleto['hora_salida']}",
                 bg=T.SURFACE, fg=T.PRIMARY, font=T.font(11, "bold")).pack(anchor="w")

        grid = tk.Frame(cuerpo, bg=T.SURFACE)
        grid.pack(fill="x", pady=(14, 4))
        datos = [("Pasajero", boleto["pasajero"]), ("Documento", f"{boleto['tipo_doc']} {boleto['num_doc']}"),
                 ("Bus", f"Unidad {boleto['unidad']} · {boleto['placa']}"),
                 ("Pago", boleto["metodo_pago"].capitalize()),
                 ("Emitido", utils.fecha_hora(boleto["fecha_emision"])), ("Atendido por", boleto["vendedor"])]
        for i, (k, v) in enumerate(datos):
            r, c = divmod(i, 2)
            tk.Label(grid, text=k.upper(), bg=T.SURFACE, fg=T.MUTED, font=T.font(8, "bold")).grid(
                row=r * 2, column=c, sticky="w", padx=(0, 30), pady=(8, 0))
            tk.Label(grid, text=v, bg=T.SURFACE, fg=T.TEXT, font=T.font(10, "bold")).grid(
                row=r * 2 + 1, column=c, sticky="w", padx=(0, 30))

        corte = tk.Canvas(papel, width=420, height=24, bg=T.SURFACE, highlightthickness=0)
        corte.pack()
        corte.create_oval(-12, 0, 12, 24, fill=T.BG, outline=T.BORDER)
        corte.create_oval(408, 0, 432, 24, fill=T.BG, outline=T.BORDER)
        corte.create_line(18, 12, 402, 12, fill="#c5d0de", dash=(5, 4))

        pie = tk.Frame(papel, bg=T.SURFACE)
        pie.pack(fill="x", padx=24, pady=(4, 18))
        a = tk.Frame(pie, bg=T.SURFACE)
        a.pack(side="left")
        tk.Label(a, text="ASIENTO", bg=T.SURFACE, fg=T.MUTED, font=T.font(8, "bold")).pack(anchor="w")
        tk.Label(a, text=f"{boleto['asiento']}", bg=T.SURFACE, fg=T.TEXT, font=T.font(26, "bold")).pack(anchor="w")
        tk.Label(a, text=utils.posicion_asiento(boleto["asiento"]), bg=T.SURFACE, fg=T.MUTED,
                 font=T.font(9)).pack(anchor="w")
        b = tk.Frame(pie, bg=T.SURFACE)
        b.pack(side="right")
        tk.Label(b, text="TOTAL", bg=T.SURFACE, fg=T.MUTED, font=T.font(8, "bold")).pack(anchor="e")
        tk.Label(b, text=utils.dinero(boleto["precio"]), bg=T.SURFACE, fg=T.SUCCESS_DARK,
                 font=T.font(22, "bold")).pack(anchor="e")

        botones = tk.Frame(self, bg=T.BG)
        botones.pack(fill="x", padx=22, pady=(0, 20))
        Button(botones, "Cerrar", self.destroy, "primary").pack(side="right")
        Button(botones, "Guardar como .txt", self._guardar, "ghost").pack(side="right", padx=8)
        self.bind("<Escape>", lambda e: self.destroy())
        self.deiconify()
        modal(self, parent)

    def _guardar(self):
        b = self.boleto
        ruta = filedialog.asksaveasfilename(parent=self, defaultextension=".txt",
                                            initialfile=f"boleto_{b['codigo']}.txt",
                                            filetypes=[("Texto", "*.txt")])
        if not ruta:
            return
        linea = "=" * 44
        texto = "\n".join([
            linea, f"  {configuracion.obtener('empresa_nombre').upper()}",
            f"  RUC {configuracion.obtener('empresa_ruc')}", "  BOLETO ELECTRÓNICO", linea,
            f"  Código    : {b['codigo']}", f"  Estado    : {b['estado'].upper()}",
            f"  Ruta      : {b['origen']} -> {b['destino']}",
            f"  Fecha     : {b['fecha']}   Salida: {b['hora_salida']}",
            f"  Bus       : Unidad {b['unidad']} ({b['placa']})",
            f"  Asiento   : {b['asiento']} ({utils.posicion_asiento(b['asiento'])})",
            f"  Pasajero  : {b['pasajero']}", f"  Documento : {b['tipo_doc']} {b['num_doc']}",
            f"  Pago      : {b['metodo_pago']}", f"  Total     : {utils.dinero(b['precio'])}",
            f"  Emitido   : {utils.fecha_hora(b['fecha_emision'])} por {b['vendedor']}", linea,
            "  Preséntese 30 minutos antes de la salida.", linea])
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(texto)
