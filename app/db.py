"""Acceso a la base de datos SQLite (una sola conexión compartida)."""
import sqlite3
from contextlib import contextmanager

from . import config
from .errors import traducir

_conn = None


def conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(config.DB_PATH)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
    return _conn


def query(sql, params=()):
    return [dict(r) for r in conn().execute(sql, params).fetchall()]


def query_one(sql, params=()):
    r = conn().execute(sql, params).fetchone()
    return dict(r) if r else None


def scalar(sql, params=(), default=None):
    r = conn().execute(sql, params).fetchone()
    return default if r is None or r[0] is None else r[0]


def execute(sql, params=()):
    """Ejecuta una instrucción en su propia transacción. Devuelve lastrowid."""
    c = conn()
    try:
        with c:
            return c.execute(sql, params).lastrowid
    except sqlite3.IntegrityError as e:
        raise traducir(e) from e


@contextmanager
def transaction():
    """Agrupa varias instrucciones: o se guardan todas o ninguna."""
    c = conn()
    try:
        yield c
        c.commit()
    except sqlite3.IntegrityError as e:
        c.rollback()
        raise traducir(e) from e
    except Exception:
        c.rollback()
        raise


def init_db():
    """Crea las tablas si no existen, carga datos demo y genera viajes."""
    c = conn()
    c.executescript(config.SCHEMA_PATH.read_text(encoding="utf-8"))
    if scalar("SELECT COUNT(*) FROM usuarios") == 0:
        from .seed import seed
        seed()
    from .services import viajes
    viajes.actualizar_estados()
    viajes.programar_desde_horarios(config.DIAS_A_PROGRAMAR)


def close():
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
