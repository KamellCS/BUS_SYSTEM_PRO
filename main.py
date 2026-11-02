"""
BUS SYSTEM PRO - Sistema de venta de pasajes y gestión de flota.

Ejecutar:   python main.py
Cuentas demo:
    Administrador -> admin    / admin123
    Trabajador    -> vendedor / vendedor123
"""
import sys

if sys.version_info < (3, 10):
    sys.exit("BUS SYSTEM PRO necesita Python 3.10 o superior.")

from app.ui.app import run

if __name__ == "__main__":
    run()
