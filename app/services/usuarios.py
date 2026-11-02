"""Gestión de usuarios (solo administrador) y cambio de contraseña propia."""
from .. import db, session, utils
from ..errors import AppError
from ..security import hash_password, verificar_password
from . import auditoria


def listar():
    return db.query("""
        SELECT u.id, u.username, u.nombres, u.apellidos, u.rol, u.activo,
               u.ultimo_acceso, u.creado_en,
               u.nombres || ' ' || u.apellidos AS nombre_completo,
               (SELECT COUNT(*) FROM boletos b WHERE b.usuario_id = u.id AND b.estado='vendido') AS ventas
          FROM usuarios u ORDER BY u.rol, u.username""")


def crear(data: dict):
    session.requiere_admin()
    username = utils.validar_username(data.get("username", ""))
    nombres = utils.validar_nombre(data.get("nombres", ""), "Nombres")
    apellidos = utils.validar_nombre(data.get("apellidos", ""), "Apellidos")
    rol = data.get("rol")
    if rol not in ("admin", "trabajador"):
        raise AppError("Selecciona un rol")
    password = utils.validar_password(data.get("password", ""))
    if password != data.get("password2", password):
        raise AppError("Las contraseñas no coinciden")
    h, salt = hash_password(password)
    nuevo = db.execute("""INSERT INTO usuarios (username, password_hash, salt, nombres, apellidos, rol)
                          VALUES (?,?,?,?,?,?)""", (username, h, salt, nombres, apellidos, rol))
    auditoria.registrar("USUARIO_CREADO", f"{username} ({rol})")
    return nuevo


def actualizar(usuario_id, data: dict):
    session.requiere_admin()
    nombres = utils.validar_nombre(data.get("nombres", ""), "Nombres")
    apellidos = utils.validar_nombre(data.get("apellidos", ""), "Apellidos")
    rol = data.get("rol")
    if rol not in ("admin", "trabajador"):
        raise AppError("Selecciona un rol")
    if usuario_id == session.usuario_id() and rol != "admin":
        raise AppError("No puedes quitarte el rol de administrador a ti mismo")
    db.execute("UPDATE usuarios SET nombres=?, apellidos=?, rol=? WHERE id=?",
               (nombres, apellidos, rol, usuario_id))
    auditoria.registrar("USUARIO_EDITADO", f"#{usuario_id}")


def restablecer_password(usuario_id, nueva: str):
    session.requiere_admin()
    utils.validar_password(nueva)
    h, salt = hash_password(nueva)
    db.execute("UPDATE usuarios SET password_hash=?, salt=? WHERE id=?", (h, salt, usuario_id))
    auditoria.registrar("PASSWORD_RESTABLECIDA", f"Usuario #{usuario_id}")


def cambiar_estado(usuario_id, activo: bool):
    session.requiere_admin()
    if usuario_id == session.usuario_id():
        raise AppError("No puedes desactivar tu propia cuenta")
    if not activo:
        admins = db.scalar("SELECT COUNT(*) FROM usuarios WHERE rol='admin' AND activo=1 AND id<>?",
                           (usuario_id,), 0)
        rol = db.scalar("SELECT rol FROM usuarios WHERE id=?", (usuario_id,))
        if rol == "admin" and admins == 0:
            raise AppError("Debe quedar al menos un administrador activo")
    db.execute("UPDATE usuarios SET activo=? WHERE id=?", (1 if activo else 0, usuario_id))
    auditoria.registrar("USUARIO_ESTADO", f"#{usuario_id} activo={activo}")


def cambiar_mi_password(actual: str, nueva: str, confirmacion: str):
    uid = session.usuario_id()
    row = db.query_one("SELECT password_hash, salt FROM usuarios WHERE id=?", (uid,))
    if not row or not verificar_password(actual, row["password_hash"], row["salt"]):
        raise AppError("La contraseña actual no es correcta")
    utils.validar_password(nueva)
    if nueva != confirmacion:
        raise AppError("La nueva contraseña y su confirmación no coinciden")
    if nueva == actual:
        raise AppError("La nueva contraseña debe ser distinta a la actual")
    h, salt = hash_password(nueva)
    db.execute("UPDATE usuarios SET password_hash=?, salt=? WHERE id=?", (h, salt, uid))
    auditoria.registrar("PASSWORD_CAMBIADA", "Cambio de contraseña propia")
