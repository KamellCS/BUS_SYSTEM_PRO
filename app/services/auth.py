"""Inicio y cierre de sesión."""
import time

from .. import config, db, session
from ..errors import AppError
from ..security import verificar_password
from . import auditoria

# usuario -> (intentos_fallidos, bloqueado_hasta)
_intentos: dict[str, tuple[int, float]] = {}


def login(username: str, password: str, rol_esperado: str | None = None) -> dict:
    username = (username or "").strip().lower()
    if not username or not password:
        raise AppError("Ingresa tu usuario y contraseña")

    fallidos, bloqueado_hasta = _intentos.get(username, (0, 0.0))
    restante = bloqueado_hasta - time.time()
    if restante > 0:
        raise AppError(f"Demasiados intentos. Espera {int(restante) + 1} segundos.")

    row = db.query_one("SELECT * FROM usuarios WHERE username = ?", (username,))
    if not row or not verificar_password(password, row["password_hash"], row["salt"]):
        fallidos += 1
        if fallidos >= config.MAX_INTENTOS_LOGIN:
            _intentos[username] = (0, time.time() + config.SEGUNDOS_BLOQUEO)
            auditoria.registrar("LOGIN_BLOQUEADO", username, row["id"] if row else None)
            raise AppError(f"Usuario bloqueado por {config.SEGUNDOS_BLOQUEO} segundos "
                           "por intentos fallidos.")
        _intentos[username] = (fallidos, 0.0)
        auditoria.registrar("LOGIN_FALLIDO", username, row["id"] if row else None)
        quedan = config.MAX_INTENTOS_LOGIN - fallidos
        raise AppError(f"Usuario o contraseña incorrectos ({quedan} intentos restantes)")

    if not row["activo"]:
        raise AppError("Tu cuenta está desactivada. Contacta al administrador.")
    if rol_esperado == "admin" and row["rol"] != "admin":
        raise AppError("Esta cuenta no tiene permisos de administrador. "
                       "Ingresa por la pestaña Trabajador.")
    if rol_esperado == "trabajador" and row["rol"] != "trabajador":
        raise AppError("Esta es una cuenta de administrador. "
                       "Ingresa por la pestaña Administrador.")

    _intentos.pop(username, None)
    db.execute("UPDATE usuarios SET ultimo_acceso = datetime('now','localtime') WHERE id = ?",
               (row["id"],))
    session.iniciar(row)
    auditoria.registrar("LOGIN", f"Ingreso como {row['rol']}")
    return row


def logout():
    if session.usuario():
        auditoria.registrar("LOGOUT", "Cierre de sesión")
    session.cerrar()
