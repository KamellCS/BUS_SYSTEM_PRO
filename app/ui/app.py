"""Arranque de la aplicación: ventana raíz, login y ventana principal."""
import traceback
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from .. import config, db
from ..services import auth
from . import icons, theme
from .login import LoginView
from .shell import Shell


class App:
    def __init__(self):
        db.init_db()
        self.root = tk.Tk()
        self.root.title(f"{config.APP_NAME} · Venta de pasajes")
        theme.init(self.root)
        self._icono = icons.window_icon(self.root)
        self.root.iconphoto(True, self._icono)
        self.root.minsize(1200, 720)
        ancho, alto = 1440, 860
        x = max((self.root.winfo_screenwidth() - ancho) // 2, 0)
        y = max((self.root.winfo_screenheight() - alto) // 3, 0)
        self.root.geometry(f"{ancho}x{alto}+{x}+{y}")
        try:
            self.root.state("zoomed")          # Windows: maximizada
        except tk.TclError:
            pass
        self.root.report_callback_exception = self._error_inesperado
        self.root.protocol("WM_DELETE_WINDOW", self._salir)
        self.pantalla = None
        self.mostrar_login()

    def _limpiar(self):
        if self.pantalla is not None:
            self.pantalla.destroy()

    def mostrar_login(self):
        self._limpiar()
        self.pantalla = LoginView(self.root, on_success=self.mostrar_principal)
        self.pantalla.pack(fill="both", expand=True)

    def mostrar_principal(self):
        self._limpiar()
        self.pantalla = Shell(self.root, on_logout=self._logout)
        self.pantalla.pack(fill="both", expand=True)

    def _logout(self):
        auth.logout()
        self.mostrar_login()

    def _salir(self):
        auth.logout()
        db.close()
        self.root.destroy()

    def _error_inesperado(self, exc, val, tb):
        detalle = "".join(traceback.format_exception(exc, val, tb))
        try:
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(config.LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}]\n{detalle}")
        except OSError:
            pass
        messagebox.showerror("Error inesperado",
                             f"{val}\n\nEl detalle se guardó en data/errores.log", parent=self.root)

    def run(self):
        self.root.mainloop()


def run():
    App().run()
