-- =====================================================================
--  BUS SYSTEM PRO - Esquema de base de datos (SQLite)
--  Todas las tablas están relacionadas mediante claves foráneas.
--
--  usuarios ─┐
--            ├──< boletos >── pasajeros
--  rutas ──< viajes >─┘
--    │        │  │
--    │        │  └── conductores
--    │        └───── buses
--    └──< horarios >── buses / conductores
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- Usuarios del sistema (login). Rol: admin | trabajador
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash  TEXT    NOT NULL,
    salt           TEXT    NOT NULL,
    nombres        TEXT    NOT NULL,
    apellidos      TEXT    NOT NULL,
    rol            TEXT    NOT NULL CHECK (rol IN ('admin', 'trabajador')),
    activo         INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    ultimo_acceso  TEXT,
    creado_en      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ---------------------------------------------------------------------
-- Configuración general (clave / valor)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS configuracion (
    clave  TEXT PRIMARY KEY,
    valor  TEXT NOT NULL
);

-- ---------------------------------------------------------------------
-- Flota de buses
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS buses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    unidad     TEXT    NOT NULL UNIQUE,
    placa      TEXT    NOT NULL UNIQUE,
    marca      TEXT    NOT NULL,
    modelo     TEXT    NOT NULL,
    anio       INTEGER NOT NULL CHECK (anio BETWEEN 1990 AND 2100),
    capacidad  INTEGER NOT NULL CHECK (capacidad BETWEEN 8 AND 80),
    estado     TEXT    NOT NULL DEFAULT 'operativo'
               CHECK (estado IN ('operativo', 'mantenimiento', 'fuera_servicio'))
);

-- ---------------------------------------------------------------------
-- Conductores
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conductores (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    dni        TEXT    NOT NULL UNIQUE CHECK (length(dni) = 8),
    nombres    TEXT    NOT NULL,
    apellidos  TEXT    NOT NULL,
    licencia   TEXT    NOT NULL UNIQUE,
    telefono   TEXT,
    activo     INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

-- ---------------------------------------------------------------------
-- Rutas (origen -> destino)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rutas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo        TEXT    NOT NULL UNIQUE,
    origen        TEXT    NOT NULL,
    destino       TEXT    NOT NULL,
    distancia_km  REAL    NOT NULL CHECK (distancia_km > 0),
    duracion_min  INTEGER NOT NULL CHECK (duracion_min > 0),
    precio_base   REAL    NOT NULL CHECK (precio_base > 0),
    activo        INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    UNIQUE (origen, destino),
    CHECK (origen <> destino)
);

-- ---------------------------------------------------------------------
-- Horarios fijos de cada ruta (plantilla para generar viajes)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS horarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ruta_id       INTEGER NOT NULL REFERENCES rutas(id)       ON DELETE CASCADE,
    hora          TEXT    NOT NULL,
    bus_id        INTEGER NOT NULL REFERENCES buses(id)       ON DELETE RESTRICT,
    conductor_id  INTEGER NOT NULL REFERENCES conductores(id) ON DELETE RESTRICT,
    activo        INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    UNIQUE (ruta_id, hora)
);

-- ---------------------------------------------------------------------
-- Viajes concretos (una salida de una ruta en una fecha y hora)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS viajes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ruta_id       INTEGER NOT NULL REFERENCES rutas(id)       ON DELETE RESTRICT,
    bus_id        INTEGER NOT NULL REFERENCES buses(id)       ON DELETE RESTRICT,
    conductor_id  INTEGER NOT NULL REFERENCES conductores(id) ON DELETE RESTRICT,
    fecha         TEXT    NOT NULL,
    hora_salida   TEXT    NOT NULL,
    precio        REAL    NOT NULL CHECK (precio > 0),
    estado        TEXT    NOT NULL DEFAULT 'programado'
                  CHECK (estado IN ('programado', 'en_ruta', 'finalizado', 'cancelado')),
    UNIQUE (ruta_id, fecha, hora_salida),
    UNIQUE (bus_id, fecha, hora_salida)
);
CREATE INDEX IF NOT EXISTS ix_viajes_fecha ON viajes(fecha);

-- ---------------------------------------------------------------------
-- Pasajeros
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pasajeros (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_doc   TEXT    NOT NULL CHECK (tipo_doc IN ('DNI', 'CE', 'PASAPORTE')),
    num_doc    TEXT    NOT NULL,
    nombres    TEXT    NOT NULL,
    apellidos  TEXT    NOT NULL,
    telefono   TEXT,
    email      TEXT,
    creado_en  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (tipo_doc, num_doc)
);

-- ---------------------------------------------------------------------
-- Boletos (venta / reserva de un asiento en un viaje)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS boletos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo         TEXT    NOT NULL UNIQUE,
    viaje_id       INTEGER NOT NULL REFERENCES viajes(id)    ON DELETE RESTRICT,
    pasajero_id    INTEGER NOT NULL REFERENCES pasajeros(id) ON DELETE RESTRICT,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios(id)  ON DELETE RESTRICT,
    asiento        INTEGER NOT NULL CHECK (asiento >= 1),
    precio         REAL    NOT NULL CHECK (precio >= 0),
    estado         TEXT    NOT NULL DEFAULT 'vendido'
                   CHECK (estado IN ('vendido', 'reservado', 'anulado')),
    metodo_pago    TEXT    NOT NULL
                   CHECK (metodo_pago IN ('efectivo', 'tarjeta', 'yape', 'plin', 'transferencia')),
    fecha_emision  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
-- Un asiento no puede estar ocupado dos veces en el mismo viaje
CREATE UNIQUE INDEX IF NOT EXISTS ux_boletos_asiento_activo
    ON boletos(viaje_id, asiento) WHERE estado <> 'anulado';
CREATE INDEX IF NOT EXISTS ix_boletos_viaje    ON boletos(viaje_id);
CREATE INDEX IF NOT EXISTS ix_boletos_pasajero ON boletos(pasajero_id);
CREATE INDEX IF NOT EXISTS ix_boletos_fecha    ON boletos(fecha_emision);

-- ---------------------------------------------------------------------
-- Auditoría (quién hizo qué y cuándo)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auditoria (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    accion      TEXT NOT NULL,
    detalle     TEXT,
    fecha       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- =====================================================================
-- TRIGGERS: reglas de negocio dentro de la base de datos
-- =====================================================================
CREATE TRIGGER IF NOT EXISTS trg_boletos_validar
BEFORE INSERT ON boletos
BEGIN
    SELECT RAISE(ABORT, 'El asiento no existe en este bus')
     WHERE NEW.asiento > (SELECT b.capacidad
                            FROM viajes v JOIN buses b ON b.id = v.bus_id
                           WHERE v.id = NEW.viaje_id);
    SELECT RAISE(ABORT, 'El viaje ya no admite ventas')
     WHERE (SELECT estado FROM viajes WHERE id = NEW.viaje_id) <> 'programado';
END;

CREATE TRIGGER IF NOT EXISTS trg_buses_capacidad
BEFORE UPDATE OF capacidad ON buses
BEGIN
    SELECT RAISE(ABORT, 'Hay boletos activos en asientos que superan la nueva capacidad')
     WHERE EXISTS (SELECT 1
                     FROM boletos bo JOIN viajes v ON v.id = bo.viaje_id
                    WHERE v.bus_id = NEW.id
                      AND bo.estado <> 'anulado'
                      AND v.estado IN ('programado', 'en_ruta')
                      AND bo.asiento > NEW.capacidad);
END;

-- =====================================================================
-- VISTAS: consultas listas para la interfaz
-- =====================================================================
CREATE VIEW IF NOT EXISTS v_viajes AS
SELECT v.id, v.fecha, v.hora_salida, v.precio, v.estado,
       r.id AS ruta_id, r.codigo AS ruta_codigo, r.origen, r.destino, r.duracion_min,
       r.origen || ' → ' || r.destino AS ruta,
       b.id AS bus_id, b.unidad, b.placa, b.capacidad,
       c.id AS conductor_id, c.nombres || ' ' || c.apellidos AS conductor,
       COALESCE(o.vendidos, 0)   AS vendidos,
       COALESCE(o.reservados, 0) AS reservados,
       b.capacidad - COALESCE(o.vendidos, 0) - COALESCE(o.reservados, 0) AS libres
  FROM viajes v
  JOIN rutas r       ON r.id = v.ruta_id
  JOIN buses b       ON b.id = v.bus_id
  JOIN conductores c ON c.id = v.conductor_id
  LEFT JOIN (SELECT viaje_id,
                    SUM(estado = 'vendido')   AS vendidos,
                    SUM(estado = 'reservado') AS reservados
               FROM boletos GROUP BY viaje_id) o ON o.viaje_id = v.id;

CREATE VIEW IF NOT EXISTS v_boletos AS
SELECT bo.id, bo.codigo, bo.asiento, bo.precio, bo.estado, bo.metodo_pago, bo.fecha_emision,
       bo.viaje_id, v.fecha, v.hora_salida, v.ruta_id,
       r.origen, r.destino, r.origen || ' → ' || r.destino AS ruta,
       b.unidad, b.placa,
       p.id AS pasajero_id, p.tipo_doc, p.num_doc, p.telefono,
       p.nombres || ' ' || p.apellidos AS pasajero,
       u.id AS usuario_id, u.nombres || ' ' || u.apellidos AS vendedor
  FROM boletos bo
  JOIN viajes v    ON v.id = bo.viaje_id
  JOIN rutas r     ON r.id = v.ruta_id
  JOIN buses b     ON b.id = v.bus_id
  JOIN pasajeros p ON p.id = bo.pasajero_id
  JOIN usuarios u  ON u.id = bo.usuario_id;
