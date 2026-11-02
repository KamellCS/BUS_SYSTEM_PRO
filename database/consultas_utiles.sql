-- Consultas de ejemplo para explorar la base de datos (DB Browser for SQLite)

-- 1. Salidas de hoy con asientos libres
SELECT hora_salida, ruta, unidad, conductor, vendidos, reservados, libres
  FROM v_viajes
 WHERE fecha = date('now', 'localtime')
 ORDER BY hora_salida;

-- 2. Ingresos por ruta (boletos pagados)
SELECT r.origen || ' → ' || r.destino AS ruta,
       COUNT(*)                       AS boletos,
       SUM(b.precio)                  AS ingresos
  FROM boletos b
  JOIN viajes v ON v.id = b.viaje_id
  JOIN rutas  r ON r.id = v.ruta_id
 WHERE b.estado = 'vendido'
 GROUP BY r.id
 ORDER BY ingresos DESC;

-- 3. Ranking de vendedores del mes
SELECT u.nombres || ' ' || u.apellidos AS vendedor, COUNT(*) AS boletos, SUM(b.precio) AS total
  FROM boletos b JOIN usuarios u ON u.id = b.usuario_id
 WHERE b.estado = 'vendido'
   AND strftime('%Y-%m', b.fecha_emision) = strftime('%Y-%m', 'now', 'localtime')
 GROUP BY u.id
 ORDER BY total DESC;

-- 4. Pasajeros frecuentes (5 viajes o más)
SELECT p.tipo_doc, p.num_doc, p.nombres || ' ' || p.apellidos AS pasajero, COUNT(*) AS viajes
  FROM pasajeros p JOIN boletos b ON b.pasajero_id = p.id
 WHERE b.estado <> 'anulado'
 GROUP BY p.id
HAVING COUNT(*) >= 5
 ORDER BY viajes DESC;

-- 5. Mapa de un viaje: quién ocupa cada asiento
SELECT asiento, estado, pasajero, num_doc, codigo
  FROM v_boletos
 WHERE viaje_id = 1 AND estado <> 'anulado'
 ORDER BY asiento;

-- 6. Reservas pendientes de pago en viajes que aún no salen
SELECT b.codigo, b.fecha, b.hora_salida, b.ruta, b.asiento, b.pasajero
  FROM v_boletos b JOIN viajes v ON v.id = b.viaje_id
 WHERE b.estado = 'reservado' AND v.estado = 'programado'
 ORDER BY b.fecha, b.hora_salida;

-- 7. Actividad reciente (auditoría)
SELECT a.fecha, COALESCE(u.username, 'sistema') AS usuario, a.accion, a.detalle
  FROM auditoria a LEFT JOIN usuarios u ON u.id = a.usuario_id
 ORDER BY a.id DESC
 LIMIT 30;
