"""Pasajeros y boletos: el corazón de la venta de pasajes."""
from .. import config, db, session, utils
from ..errors import AppError
from . import auditoria, viajes

# ============================================================== PASAJEROS
def listar_pasajeros(filtro: str = ""):
    filtro = f"%{filtro.strip()}%"
    return db.query("""
        SELECT p.*, p.nombres || ' ' || p.apellidos AS nombre_completo,
               (SELECT COUNT(*) FROM boletos b
                 WHERE b.pasajero_id = p.id AND b.estado <> 'anulado') AS viajes
          FROM pasajeros p
         WHERE p.num_doc LIKE ? OR p.nombres LIKE ? OR p.apellidos LIKE ?
            OR (p.nombres || ' ' || p.apellidos) LIKE ?
         ORDER BY p.apellidos, p.nombres""", (filtro,) * 4)


def buscar_pasajero(tipo_doc: str, num_doc: str):
    if not num_doc.strip():
        return None
    p = db.query_one("SELECT * FROM pasajeros WHERE tipo_doc=? AND num_doc=?",
                     (tipo_doc, num_doc.strip().upper()))
    if p:
        p["viajes"] = db.scalar("SELECT COUNT(*) FROM boletos WHERE pasajero_id=? AND estado<>'anulado'",
                                (p["id"],), 0)
    return p


def _validar_pasajero(data: dict) -> tuple:
    tipo = data.get("tipo_doc", "DNI")
    return (
        tipo,
        utils.validar_documento(tipo, data.get("num_doc", "")),
        utils.validar_nombre(data.get("nombres", ""), "Nombres"),
        utils.validar_nombre(data.get("apellidos", ""), "Apellidos"),
        utils.validar_telefono(data.get("telefono", "")),
        utils.validar_email(data.get("email", "")),
    )


def guardar_pasajero(data: dict, pasajero_id=None):
    valores = _validar_pasajero(data)
    if pasajero_id:
        db.execute("""UPDATE pasajeros SET tipo_doc=?, num_doc=?, nombres=?, apellidos=?,
                      telefono=?, email=? WHERE id=?""", valores + (pasajero_id,))
        auditoria.registrar("PASAJERO_EDITADO", f"{valores[0]} {valores[1]}")
        return pasajero_id
    nuevo = db.execute("""INSERT INTO pasajeros (tipo_doc, num_doc, nombres, apellidos, telefono, email)
                          VALUES (?,?,?,?,?,?)""", valores)
    auditoria.registrar("PASAJERO_CREADO", f"{valores[0]} {valores[1]}")
    return nuevo


def eliminar_pasajero(pasajero_id):
    session.requiere_admin()
    db.execute("DELETE FROM pasajeros WHERE id=?", (pasajero_id,))
    auditoria.registrar("PASAJERO_ELIMINADO", f"#{pasajero_id}")


def historial_pasajero(pasajero_id):
    return db.query("""SELECT * FROM v_boletos WHERE pasajero_id=?
                        ORDER BY fecha DESC, hora_salida DESC""", (pasajero_id,))


# ============================================================== BOLETOS
def emitir_boleto(viaje_id, asiento, datos_pasajero: dict, metodo_pago: str,
                  estado: str = "vendido") -> dict:
    """Vende o reserva un asiento. Todo ocurre en UNA transacción."""
    if not session.usuario():
        raise AppError("Debes iniciar sesión")
    if estado not in ("vendido", "reservado"):
        raise AppError("Estado de boleto inválido")
    if metodo_pago not in config.METODOS_PAGO:
        raise AppError("Selecciona un método de pago")
    if not viaje_id:
        raise AppError("Selecciona un viaje")
    if not asiento:
        raise AppError("Selecciona un asiento en el mapa")

    viajes.actualizar_estados()
    viaje = viajes.obtener(viaje_id)
    if not viaje or viaje["estado"] != "programado":
        raise AppError("Este viaje ya salió o fue cancelado")
    valores = _validar_pasajero(datos_pasajero)

    with db.transaction() as c:
        fila = c.execute("SELECT id FROM pasajeros WHERE tipo_doc=? AND num_doc=?",
                         valores[:2]).fetchone()
        if fila:
            pasajero_id = fila["id"]
            c.execute("""UPDATE pasajeros SET nombres=?, apellidos=?,
                         telefono=COALESCE(NULLIF(?, ''), telefono),
                         email=COALESCE(NULLIF(?, ''), email) WHERE id=?""",
                      valores[2:] + (pasajero_id,))
        else:
            pasajero_id = c.execute("""INSERT INTO pasajeros
                                       (tipo_doc, num_doc, nombres, apellidos, telefono, email)
                                       VALUES (?,?,?,?,?,?)""", valores).lastrowid

        repetido = c.execute("""SELECT asiento FROM boletos WHERE viaje_id=? AND pasajero_id=?
                                AND estado<>'anulado'""", (viaje_id, pasajero_id)).fetchone()
        if repetido:
            raise AppError(f"Este pasajero ya tiene el asiento {repetido['asiento']} en este viaje")

        codigo = utils.generar_codigo_boleto(viaje_id, asiento)
        while c.execute("SELECT 1 FROM boletos WHERE codigo=?", (codigo,)).fetchone():
            codigo = utils.generar_codigo_boleto(viaje_id, asiento)

        boleto_id = c.execute("""
            INSERT INTO boletos (codigo, viaje_id, pasajero_id, usuario_id, asiento, precio,
                                 estado, metodo_pago)
            VALUES (?,?,?,?,?,?,?,?)""",
            (codigo, viaje_id, pasajero_id, session.usuario_id(), int(asiento),
             viaje["precio"], estado, metodo_pago)).lastrowid
        auditoria.registrar("BOLETO_" + estado.upper(),
                            f"{codigo} · {viaje['ruta']} · asiento {asiento}", conexion=c)
    return detalle_boleto(boleto_id)


def detalle_boleto(boleto_id):
    return db.query_one("SELECT * FROM v_boletos WHERE id=?", (boleto_id,))


def confirmar_reserva(boleto_id, metodo_pago=None):
    b = detalle_boleto(boleto_id)
    if not b or b["estado"] != "reservado":
        raise AppError("Solo se pueden confirmar boletos reservados")
    viajes.actualizar_estados()
    if viajes.obtener(b["viaje_id"])["estado"] != "programado":
        raise AppError("El viaje ya salió; la reserva venció")
    metodo = metodo_pago if metodo_pago in config.METODOS_PAGO else b["metodo_pago"]
    db.execute("""UPDATE boletos SET estado='vendido', metodo_pago=?,
                  fecha_emision=datetime('now','localtime') WHERE id=?""", (metodo, boleto_id))
    auditoria.registrar("RESERVA_PAGADA", b["codigo"])
    return detalle_boleto(boleto_id)


def anular_boleto(boleto_id):
    b = detalle_boleto(boleto_id)
    if not b or b["estado"] == "anulado":
        raise AppError("El boleto ya está anulado")
    if b["estado"] == "vendido":
        session.requiere_admin()        # anular una venta pagada es solo para admin
    db.execute("UPDATE boletos SET estado='anulado' WHERE id=?", (boleto_id,))
    auditoria.registrar("BOLETO_ANULADO", f"{b['codigo']} · asiento {b['asiento']}")


def ultimas_ventas(limite=8):
    return db.query("""SELECT * FROM v_boletos WHERE estado <> 'anulado'
                        ORDER BY fecha_emision DESC, id DESC LIMIT ?""", (limite,))


def reservas_pendientes():
    return db.query("""SELECT bo.* FROM v_boletos bo JOIN viajes v ON v.id = bo.viaje_id
                        WHERE bo.estado='reservado' AND v.estado='programado'
                        ORDER BY bo.fecha, bo.hora_salida""")
