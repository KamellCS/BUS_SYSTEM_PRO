"""Registro de actividad (auditoría)."""
from .. import db, session


def registrar(accion: str, detalle: str = "", usuario_id=None, conexion=None):
    uid = usuario_id if usuario_id is not None else session.usuario_id()
    sql = "INSERT INTO auditoria (usuario_id, accion, detalle) VALUES (?, ?, ?)"
    if conexion is not None:           # dentro de una transacción en curso
        conexion.execute(sql, (uid, accion, detalle))
    else:
        db.execute(sql, (uid, accion, detalle))


def recientes(limite=60):
    return db.query("""
        SELECT a.fecha, a.accion, a.detalle,
               COALESCE(u.username, '—') AS usuario
          FROM auditoria a LEFT JOIN usuarios u ON u.id = a.usuario_id
         ORDER BY a.id DESC LIMIT ?""", (limite,))
