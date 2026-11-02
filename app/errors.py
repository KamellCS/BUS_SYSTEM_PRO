"""Errores de negocio que la interfaz muestra al usuario."""
import sqlite3


class AppError(Exception):
    """Error esperado (validación, permiso, regla de negocio)."""


_MENSAJES_UNIQUE = {
    "usuarios.username": "Ya existe un usuario con ese nombre",
    "buses.placa": "Ya existe un bus con esa placa",
    "buses.unidad": "Ya existe un bus con ese número de unidad",
    "conductores.dni": "Ya existe un conductor con ese DNI",
    "conductores.licencia": "Ya existe un conductor con esa licencia",
    "rutas.codigo": "Ya existe una ruta con ese código",
    "rutas.origen, rutas.destino": "Esa ruta (origen → destino) ya existe",
    "horarios.ruta_id, horarios.hora": "La ruta ya tiene un horario a esa hora",
    "viajes.ruta_id, viajes.fecha, viajes.hora_salida": "Ya hay un viaje de esa ruta en esa fecha y hora",
    "viajes.bus_id, viajes.fecha, viajes.hora_salida": "Ese bus ya tiene un viaje en esa fecha y hora",
    "pasajeros.tipo_doc, pasajeros.num_doc": "Ya existe un pasajero con ese documento",
    "boletos.viaje_id, boletos.asiento": "Ese asiento acaba de ser ocupado. Elige otro",
}


def traducir(e: sqlite3.IntegrityError) -> AppError:
    """Convierte errores técnicos de SQLite en mensajes entendibles."""
    msg = str(e)
    if "UNIQUE constraint failed" in msg:
        campos = msg.split("failed:")[-1].strip()
        return AppError(_MENSAJES_UNIQUE.get(campos, "El registro ya existe"))
    if "FOREIGN KEY constraint failed" in msg:
        return AppError("No se puede completar: el registro está relacionado con otros datos "
                        "(viajes, boletos u horarios).")
    if "CHECK constraint failed" in msg:
        return AppError("Hay un valor fuera de rango. Revisa los datos ingresados.")
    return AppError(msg)
