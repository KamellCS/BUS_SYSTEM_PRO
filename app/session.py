"""Usuario que tiene la sesión abierta."""
from .errors import AppError

_usuario = None


def iniciar(row: dict):
    global _usuario
    _usuario = {k: row[k] for k in ("id", "username", "nombres", "apellidos", "rol")}


def cerrar():
    global _usuario
    _usuario = None


def usuario() -> dict | None:
    return _usuario


def usuario_id():
    return _usuario["id"] if _usuario else None


def es_admin() -> bool:
    return bool(_usuario and _usuario["rol"] == "admin")


def requiere_admin():
    if not es_admin():
        raise AppError("Solo el administrador puede realizar esta acción.")


def nombre_corto() -> str:
    if not _usuario:
        return ""
    return f"{_usuario['nombres'].split()[0]} {_usuario['apellidos'].split()[0]}"
