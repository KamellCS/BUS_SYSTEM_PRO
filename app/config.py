"""Configuración global: rutas de archivos y constantes del sistema."""
from pathlib import Path

# Rutas calculadas a partir de este archivo: funciona sin importar
# desde qué carpeta se ejecute el programa (Visual Studio, terminal, etc.)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"
DB_PATH = DATA_DIR / "bus_system.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
LOG_PATH = DATA_DIR / "errores.log"

APP_NAME = "BUS SYSTEM PRO"
APP_VERSION = "3.0"
EMPRESA_DEFAULT = "Empresa de Buses El Sol"
MONEDA = "S/"

DIAS_A_PROGRAMAR = 7          # viajes generados automáticamente hacia adelante
MAX_INTENTOS_LOGIN = 5        # intentos fallidos antes de bloquear
SEGUNDOS_BLOQUEO = 30

METODOS_PAGO = ["efectivo", "tarjeta", "yape", "plin", "transferencia"]
TIPOS_DOC = ["DNI", "CE", "PASAPORTE"]
ESTADOS_BUS = ["operativo", "mantenimiento", "fuera_servicio"]
