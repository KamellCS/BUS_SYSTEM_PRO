"""Viajes: programación, estados y ocupación de asientos."""
from datetime import date, datetime, timedelta

from .. import db, session, utils
from ..errors import AppError
from . import auditoria


def actualizar_estados():
    """Pone en ruta / finaliza los viajes según la hora actual."""
    with db.transaction() as c:
        c.execute("""
            UPDATE viajes SET estado = 'finalizado'
             WHERE estado IN ('programado', 'en_ruta')
               AND datetime(fecha || ' ' || hora_salida,
                            '+' || (SELECT duracion_min FROM rutas r WHERE r.id = viajes.ruta_id)
                            || ' minutes') <= datetime('now', 'localtime')""")
        c.execute("""
            UPDATE viajes SET estado = 'en_ruta'
             WHERE estado = 'programado'
               AND datetime(fecha || ' ' || hora_salida) <= datetime('now', 'localtime')""")
        # Las reservas no pagadas vencen cuando el bus sale
        c.execute("""
            UPDATE boletos SET estado = 'anulado'
             WHERE estado = 'reservado'
               AND viaje_id IN (SELECT id FROM viajes WHERE estado <> 'programado')""")


def programar_desde_horarios(dias=7, desde: date | None = None) -> int:
    """Crea los viajes de los próximos días a partir de los horarios fijos."""
    desde = desde or date.today()
    c = db.conn()
    antes = c.total_changes
    with db.transaction() as c:
        for i in range(dias):
            fecha = (desde + timedelta(days=i)).isoformat()
            c.execute("""
                INSERT OR IGNORE INTO viajes (ruta_id, bus_id, conductor_id, fecha, hora_salida, precio)
                SELECT h.ruta_id, h.bus_id, h.conductor_id, ?, h.hora, r.precio_base
                  FROM horarios h
                  JOIN rutas r       ON r.id = h.ruta_id AND r.activo = 1
                  JOIN buses b       ON b.id = h.bus_id AND b.estado = 'operativo'
                  JOIN conductores k ON k.id = h.conductor_id AND k.activo = 1
                 WHERE h.activo = 1""", (fecha,))
    return c.total_changes - antes


def listar(fecha: str | None = None, desde: str | None = None, solo_vendibles=False):
    filtros, params = [], []
    if fecha:
        filtros.append("fecha = ?"); params.append(fecha)
    if desde:
        filtros.append("fecha >= ?"); params.append(desde)
    if solo_vendibles:
        filtros.append("estado = 'programado'")
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    return db.query(f"SELECT * FROM v_viajes {where} ORDER BY fecha, hora_salida, ruta", params)


def obtener(viaje_id):
    return db.query_one("SELECT * FROM v_viajes WHERE id = ?", (viaje_id,))


def de_hoy():
    return listar(fecha=date.today().isoformat())


def proximo_de_hoy():
    """Siguiente salida de hoy (o la última si ya salieron todas)."""
    viajes = [v for v in de_hoy() if v["estado"] != "cancelado"]
    pendientes = [v for v in viajes if v["estado"] == "programado"]
    if pendientes:
        return pendientes[0]
    futuros = listar(desde=date.today().isoformat(), solo_vendibles=True)
    return futuros[0] if futuros else (viajes[-1] if viajes else None)


def ocupacion(viaje_id) -> dict:
    """{asiento: fila_boleto} de los asientos ocupados o reservados."""
    filas = db.query("""SELECT * FROM v_boletos
                         WHERE viaje_id = ? AND estado <> 'anulado'""", (viaje_id,))
    return {f["asiento"]: f for f in filas}


def fechas_disponibles(dias=7):
    hoy = date.today()
    return [(hoy + timedelta(days=i)).isoformat() for i in range(dias)]


def crear_manual(data: dict):
    session.requiere_admin()
    fecha = utils.validar_fecha(data.get("fecha", ""))
    hora = utils.validar_hora(data.get("hora_salida", ""))
    if datetime.fromisoformat(f"{fecha} {hora}") <= datetime.now():
        raise AppError("La fecha y hora de salida deben ser futuras")
    ruta_id = int(utils.requerido(str(data.get("ruta_id") or ""), "Ruta"))
    bus_id = int(utils.requerido(str(data.get("bus_id") or ""), "Bus"))
    conductor_id = int(utils.requerido(str(data.get("conductor_id") or ""), "Conductor"))
    precio = utils.a_decimal(data.get("precio"), "Precio", 1)
    nuevo = db.execute("""INSERT INTO viajes (ruta_id, bus_id, conductor_id, fecha, hora_salida, precio)
                          VALUES (?,?,?,?,?,?)""", (ruta_id, bus_id, conductor_id, fecha, hora, precio))
    auditoria.registrar("VIAJE_CREADO", f"Viaje #{nuevo} {fecha} {hora}")
    return nuevo


def cancelar(viaje_id):
    session.requiere_admin()
    v = obtener(viaje_id)
    if not v:
        raise AppError("Viaje no encontrado")
    if v["estado"] != "programado":
        raise AppError("Solo se pueden cancelar viajes programados")
    with db.transaction() as c:
        c.execute("UPDATE viajes SET estado='cancelado' WHERE id=?", (viaje_id,))
        c.execute("UPDATE boletos SET estado='anulado' WHERE viaje_id=? AND estado<>'anulado'",
                  (viaje_id,))
        auditoria.registrar("VIAJE_CANCELADO",
                            f"#{viaje_id} {v['ruta']} {v['fecha']} {v['hora_salida']} "
                            f"({v['vendidos'] + v['reservados']} boletos anulados)", conexion=c)
