"""Datos de la empresa y respaldo de la base de datos."""
import sqlite3
from datetime import datetime

from .. import config, db, session, utils
from ..errors import AppError
from . import auditoria

CLAVES = {
    "empresa_nombre": config.EMPRESA_DEFAULT,
    "empresa_ruc": "20512345678",
    "empresa_telefono": "(01) 555-0101",
    "empresa_direccion": "Av. Javier Prado Este 1234, Lima",
}


def obtener(clave: str) -> str:
    valor = db.scalar("SELECT valor FROM configuracion WHERE clave=?", (clave,))
    return valor if valor is not None else CLAVES.get(clave, "")


def todo() -> dict:
    return {k: obtener(k) for k in CLAVES}


def guardar_empresa(data: dict):
    session.requiere_admin()
    nombre = utils.requerido(data.get("empresa_nombre"), "Nombre de la empresa")
    ruc = data.get("empresa_ruc", "").strip()
    if ruc and (not ruc.isdigit() or len(ruc) != 11):
        raise AppError("El RUC debe tener 11 dígitos")
    valores = {"empresa_nombre": nombre, "empresa_ruc": ruc,
               "empresa_telefono": data.get("empresa_telefono", "").strip(),
               "empresa_direccion": data.get("empresa_direccion", "").strip()}
    with db.transaction() as c:
        for k, v in valores.items():
            c.execute("INSERT INTO configuracion (clave, valor) VALUES (?, ?) "
                      "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor", (k, v))
        auditoria.registrar("EMPRESA_ACTUALIZADA", nombre, conexion=c)


def estadisticas_bd() -> list[tuple[str, int]]:
    tablas = ["usuarios", "buses", "conductores", "rutas", "horarios",
              "viajes", "pasajeros", "boletos", "auditoria"]
    return [(t, db.scalar(f"SELECT COUNT(*) FROM {t}", default=0)) for t in tablas]


def tamanio_bd_kb() -> float:
    return config.DB_PATH.stat().st_size / 1024 if config.DB_PATH.exists() else 0


def crear_respaldo() -> str:
    """Copia segura de la base de datos usando la API de backup de SQLite."""
    session.requiere_admin()
    config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    destino = config.BACKUP_DIR / f"bus_system_{datetime.now():%Y%m%d_%H%M%S}.db"
    with sqlite3.connect(destino) as copia:
        db.conn().backup(copia)
    copia.close()
    auditoria.registrar("RESPALDO_BD", destino.name)
    return str(destino)
