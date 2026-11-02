"""Indicadores del tablero e informes de ventas."""
import csv
from datetime import date, timedelta

from .. import db, session, utils
from . import auditoria


def kpis_hoy() -> dict:
    hoy = date.today().isoformat()
    viajes_hoy = db.query("SELECT * FROM v_viajes WHERE fecha=? AND estado<>'cancelado'", (hoy,))
    capacidad = sum(v["capacidad"] for v in viajes_hoy)
    ocupados = sum(v["vendidos"] + v["reservados"] for v in viajes_hoy)
    ventas = db.query_one("""SELECT COUNT(*) AS n, COALESCE(SUM(precio),0) AS total FROM boletos
                              WHERE estado='vendido' AND date(fecha_emision)=?""", (hoy,))
    return {
        "viajes": len(viajes_hoy),
        "por_salir": sum(1 for v in viajes_hoy if v["estado"] == "programado"),
        "pasajeros": db.scalar("SELECT COUNT(*) FROM pasajeros", default=0),
        "pasajeros_nuevos": db.scalar("SELECT COUNT(*) FROM pasajeros WHERE date(creado_en)=?",
                                      (hoy,), 0),
        "ventas_hoy": ventas["total"],
        "boletos_hoy": ventas["n"],
        "ocupacion": (ocupados / capacidad * 100) if capacidad else 0,
        "asientos_ocupados": ocupados,
        "asientos_total": capacidad,
    }


def _desde(dias: int | None) -> str:
    if dias is None:
        return "0000-01-01"
    return (date.today() - timedelta(days=max(dias - 1, 0))).isoformat()


def resumen(dias: int | None) -> dict:
    desde = _desde(dias)
    r = db.query_one("""
        SELECT COALESCE(SUM(CASE WHEN estado='vendido' THEN precio END),0) AS ingresos,
               SUM(estado='vendido')  AS vendidos,
               SUM(estado='anulado')  AS anulados
          FROM boletos WHERE date(fecha_emision) >= ?""", (desde,))
    vendidos = r["vendidos"] or 0
    return {
        "ingresos": r["ingresos"],
        "vendidos": vendidos,
        "anulados": r["anulados"] or 0,
        "promedio": (r["ingresos"] / vendidos) if vendidos else 0,
        "reservas": db.scalar("""SELECT COUNT(*) FROM boletos bo JOIN viajes v ON v.id=bo.viaje_id
                                 WHERE bo.estado='reservado' AND v.estado='programado'""", default=0),
    }


def ingresos_por_dia(dias: int) -> list[tuple[str, float]]:
    desde = date.today() - timedelta(days=dias - 1)
    filas = db.query("""SELECT date(fecha_emision) AS dia, SUM(precio) AS total FROM boletos
                         WHERE estado='vendido' AND date(fecha_emision) >= ?
                         GROUP BY dia""", (desde.isoformat(),))
    por_dia = {f["dia"]: f["total"] for f in filas}
    salida = []
    for i in range(dias):
        d = desde + timedelta(days=i)
        salida.append((f"{d.day:02d}/{d.month:02d}", por_dia.get(d.isoformat(), 0.0)))
    return salida


def ventas_por_ruta(dias: int | None):
    filas = db.query("""
        SELECT r.codigo, r.origen || ' → ' || r.destino AS ruta,
               COUNT(*) AS boletos, SUM(bo.precio) AS ingresos
          FROM boletos bo JOIN viajes v ON v.id=bo.viaje_id JOIN rutas r ON r.id=v.ruta_id
         WHERE bo.estado='vendido' AND date(bo.fecha_emision) >= ?
         GROUP BY r.id""", (_desde(dias),))
    return utils.merge_sort(filas, key=lambda f: f["ingresos"], reverse=True)


def ventas_por_vendedor(dias: int | None):
    filas = db.query("""
        SELECT u.username, u.nombres || ' ' || u.apellidos AS vendedor, u.rol,
               COUNT(*) AS boletos, SUM(bo.precio) AS ingresos
          FROM boletos bo JOIN usuarios u ON u.id=bo.usuario_id
         WHERE bo.estado='vendido' AND date(bo.fecha_emision) >= ?
         GROUP BY u.id""", (_desde(dias),))
    return utils.merge_sort(filas, key=lambda f: f["ingresos"], reverse=True)


def ventas_por_metodo(dias: int | None):
    filas = db.query("""SELECT metodo_pago, COUNT(*) AS boletos, SUM(precio) AS ingresos
                          FROM boletos WHERE estado='vendido' AND date(fecha_emision) >= ?
                         GROUP BY metodo_pago""", (_desde(dias),))
    return utils.merge_sort(filas, key=lambda f: f["ingresos"], reverse=True)


def exportar_csv(ruta_archivo: str, dias: int | None) -> int:
    session.requiere_admin()
    filas = db.query("""SELECT codigo, fecha_emision, ruta, fecha, hora_salida, unidad, asiento,
                               tipo_doc, num_doc, pasajero, precio, metodo_pago, estado, vendedor
                          FROM v_boletos WHERE date(fecha_emision) >= ?
                         ORDER BY fecha_emision""", (_desde(dias),))
    columnas = ["codigo", "fecha_emision", "ruta", "fecha", "hora_salida", "unidad", "asiento",
                "tipo_doc", "num_doc", "pasajero", "precio", "metodo_pago", "estado", "vendedor"]
    with open(ruta_archivo, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columnas, delimiter=";")
        w.writeheader()
        w.writerows(filas)
    auditoria.registrar("EXPORTACION_CSV", f"{len(filas)} boletos")
    return len(filas)
