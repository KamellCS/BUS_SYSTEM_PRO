"""Buses, conductores, rutas y horarios (datos maestros)."""
from datetime import date

from .. import config, db, session, utils
from ..errors import AppError
from . import auditoria

# ============================================================== BUSES
def listar_buses(solo_operativos=False):
    where = "WHERE b.estado = 'operativo'" if solo_operativos else ""
    return db.query(f"""
        SELECT b.*,
               (SELECT COUNT(*) FROM viajes v
                 WHERE v.bus_id = b.id AND v.estado = 'programado') AS viajes_programados
          FROM buses b {where}
         ORDER BY b.unidad""")


def guardar_bus(data: dict, bus_id=None):
    session.requiere_admin()
    valores = (
        utils.requerido(data.get("unidad"), "Unidad").upper(),
        utils.validar_placa(data.get("placa", "")),
        utils.requerido(data.get("marca"), "Marca"),
        utils.requerido(data.get("modelo"), "Modelo"),
        utils.a_entero(data.get("anio"), "Año", 1990, date.today().year + 1),
        utils.a_entero(data.get("capacidad"), "Capacidad", 8, 80),
        data.get("estado") if data.get("estado") in config.ESTADOS_BUS else "operativo",
    )
    if bus_id:
        db.execute("""UPDATE buses SET unidad=?, placa=?, marca=?, modelo=?, anio=?,
                      capacidad=?, estado=? WHERE id=?""", valores + (bus_id,))
        auditoria.registrar("BUS_EDITADO", f"Unidad {valores[0]}")
        return bus_id
    nuevo = db.execute("""INSERT INTO buses (unidad, placa, marca, modelo, anio, capacidad, estado)
                          VALUES (?,?,?,?,?,?,?)""", valores)
    auditoria.registrar("BUS_CREADO", f"Unidad {valores[0]} · {valores[1]}")
    return nuevo


def cambiar_estado_bus(bus_id, estado):
    session.requiere_admin()
    if estado not in config.ESTADOS_BUS:
        raise AppError("Estado inválido")
    db.execute("UPDATE buses SET estado=? WHERE id=?", (estado, bus_id))
    auditoria.registrar("BUS_ESTADO", f"Bus #{bus_id} → {estado}")


def eliminar_bus(bus_id):
    session.requiere_admin()
    db.execute("DELETE FROM buses WHERE id=?", (bus_id,))
    auditoria.registrar("BUS_ELIMINADO", f"Bus #{bus_id}")


# ============================================================== CONDUCTORES
def listar_conductores(solo_activos=False):
    where = "WHERE c.activo = 1" if solo_activos else ""
    return db.query(f"""
        SELECT c.*, c.nombres || ' ' || c.apellidos AS nombre_completo,
               (SELECT COUNT(*) FROM viajes v
                 WHERE v.conductor_id = c.id AND v.estado = 'programado') AS viajes_programados
          FROM conductores c {where}
         ORDER BY c.apellidos, c.nombres""")


def guardar_conductor(data: dict, conductor_id=None):
    session.requiere_admin()
    valores = (
        utils.validar_dni(data.get("dni", "")),
        utils.validar_nombre(data.get("nombres", ""), "Nombres"),
        utils.validar_nombre(data.get("apellidos", ""), "Apellidos"),
        utils.requerido(data.get("licencia"), "Licencia").upper(),
        utils.validar_telefono(data.get("telefono", "")),
    )
    if conductor_id:
        db.execute("""UPDATE conductores SET dni=?, nombres=?, apellidos=?, licencia=?, telefono=?
                      WHERE id=?""", valores + (conductor_id,))
        auditoria.registrar("CONDUCTOR_EDITADO", f"{valores[1]} {valores[2]}")
        return conductor_id
    nuevo = db.execute("""INSERT INTO conductores (dni, nombres, apellidos, licencia, telefono)
                          VALUES (?,?,?,?,?)""", valores)
    auditoria.registrar("CONDUCTOR_CREADO", f"{valores[1]} {valores[2]}")
    return nuevo


def cambiar_estado_conductor(conductor_id, activo: bool):
    session.requiere_admin()
    db.execute("UPDATE conductores SET activo=? WHERE id=?", (1 if activo else 0, conductor_id))
    auditoria.registrar("CONDUCTOR_ESTADO", f"#{conductor_id} activo={activo}")


def eliminar_conductor(conductor_id):
    session.requiere_admin()
    db.execute("DELETE FROM conductores WHERE id=?", (conductor_id,))
    auditoria.registrar("CONDUCTOR_ELIMINADO", f"#{conductor_id}")


# ============================================================== RUTAS
def listar_rutas(solo_activas=False):
    where = "WHERE r.activo = 1" if solo_activas else ""
    return db.query(f"""
        SELECT r.*, r.origen || ' → ' || r.destino AS nombre,
               (SELECT COUNT(*) FROM horarios h WHERE h.ruta_id = r.id AND h.activo = 1) AS num_horarios
          FROM rutas r {where}
         ORDER BY r.codigo""")


def guardar_ruta(data: dict, ruta_id=None):
    session.requiere_admin()
    origen = utils.validar_nombre(data.get("origen", ""), "Origen")
    destino = utils.validar_nombre(data.get("destino", ""), "Destino")
    if origen == destino:
        raise AppError("El origen y el destino deben ser diferentes")
    valores = (
        utils.requerido(data.get("codigo"), "Código").upper(),
        origen, destino,
        utils.a_decimal(data.get("distancia_km"), "Distancia", 1),
        utils.a_entero(data.get("duracion_min"), "Duración (min)", 10, 3000),
        utils.a_decimal(data.get("precio_base"), "Precio", 1),
    )
    if ruta_id:
        db.execute("""UPDATE rutas SET codigo=?, origen=?, destino=?, distancia_km=?,
                      duracion_min=?, precio_base=? WHERE id=?""", valores + (ruta_id,))
        auditoria.registrar("RUTA_EDITADA", f"{valores[0]} {origen} → {destino}")
        return ruta_id
    nuevo = db.execute("""INSERT INTO rutas (codigo, origen, destino, distancia_km, duracion_min, precio_base)
                          VALUES (?,?,?,?,?,?)""", valores)
    auditoria.registrar("RUTA_CREADA", f"{valores[0]} {origen} → {destino}")
    return nuevo


def eliminar_ruta(ruta_id):
    session.requiere_admin()
    db.execute("DELETE FROM rutas WHERE id=?", (ruta_id,))
    auditoria.registrar("RUTA_ELIMINADA", f"Ruta #{ruta_id}")


# ============================================================== HORARIOS
def listar_horarios(ruta_id):
    return db.query("""
        SELECT h.*, b.unidad, b.placa, c.nombres || ' ' || c.apellidos AS conductor
          FROM horarios h
          JOIN buses b ON b.id = h.bus_id
          JOIN conductores c ON c.id = h.conductor_id
         WHERE h.ruta_id = ?
         ORDER BY h.hora""", (ruta_id,))


def guardar_horario(data: dict, horario_id=None):
    session.requiere_admin()
    valores = (
        int(utils.requerido(str(data.get("ruta_id") or ""), "Ruta")),
        utils.validar_hora(data.get("hora", "")),
        int(utils.requerido(str(data.get("bus_id") or ""), "Bus")),
        int(utils.requerido(str(data.get("conductor_id") or ""), "Conductor")),
    )
    if horario_id:
        db.execute("UPDATE horarios SET ruta_id=?, hora=?, bus_id=?, conductor_id=? WHERE id=?",
                   valores + (horario_id,))
        return horario_id
    nuevo = db.execute("INSERT INTO horarios (ruta_id, hora, bus_id, conductor_id) VALUES (?,?,?,?)",
                       valores)
    auditoria.registrar("HORARIO_CREADO", f"Ruta #{valores[0]} {valores[1]}")
    return nuevo


def eliminar_horario(horario_id):
    session.requiere_admin()
    db.execute("DELETE FROM horarios WHERE id=?", (horario_id,))
    auditoria.registrar("HORARIO_ELIMINADO", f"Horario #{horario_id}")
