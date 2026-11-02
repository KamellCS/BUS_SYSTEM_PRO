# Diagrama de la base de datos

Motor: **SQLite** · Archivo: `data/bus_system.db` · Esquema: `schema.sql`

```mermaid
erDiagram
    USUARIOS ||--o{ BOLETOS : "vende"
    USUARIOS ||--o{ AUDITORIA : "registra"
    PASAJEROS ||--o{ BOLETOS : "compra"
    VIAJES ||--o{ BOLETOS : "tiene"
    RUTAS ||--o{ VIAJES : "se programa en"
    BUSES ||--o{ VIAJES : "realiza"
    CONDUCTORES ||--o{ VIAJES : "conduce"
    RUTAS ||--o{ HORARIOS : "tiene"
    BUSES ||--o{ HORARIOS : "asignado a"
    CONDUCTORES ||--o{ HORARIOS : "asignado a"

    USUARIOS {
        int id PK
        text username UK
        text password_hash
        text salt
        text nombres
        text apellidos
        text rol "admin | trabajador"
        int activo
        text ultimo_acceso
    }
    BUSES {
        int id PK
        text unidad UK
        text placa UK
        text marca
        text modelo
        int anio
        int capacidad
        text estado "operativo | mantenimiento | fuera_servicio"
    }
    CONDUCTORES {
        int id PK
        text dni UK
        text nombres
        text apellidos
        text licencia UK
        text telefono
        int activo
    }
    RUTAS {
        int id PK
        text codigo UK
        text origen
        text destino
        real distancia_km
        int duracion_min
        real precio_base
    }
    HORARIOS {
        int id PK
        int ruta_id FK
        text hora
        int bus_id FK
        int conductor_id FK
    }
    VIAJES {
        int id PK
        int ruta_id FK
        int bus_id FK
        int conductor_id FK
        text fecha
        text hora_salida
        real precio
        text estado "programado | en_ruta | finalizado | cancelado"
    }
    PASAJEROS {
        int id PK
        text tipo_doc "DNI | CE | PASAPORTE"
        text num_doc
        text nombres
        text apellidos
        text telefono
        text email
    }
    BOLETOS {
        int id PK
        text codigo UK
        int viaje_id FK
        int pasajero_id FK
        int usuario_id FK
        int asiento
        real precio
        text estado "vendido | reservado | anulado"
        text metodo_pago
        text fecha_emision
    }
    AUDITORIA {
        int id PK
        int usuario_id FK
        text accion
        text detalle
        text fecha
    }
```

> El bloque de arriba se ve como diagrama en GitHub, en VS Code (con la extensión *Markdown Preview Mermaid*) o pegándolo en https://mermaid.live

## Cómo se relaciona todo

- Un **viaje** es una salida concreta: *ruta + bus + conductor + fecha + hora*.
- Un **boleto** une un **viaje**, un **pasajero** y el **usuario** que lo vendió, en un **asiento**.
- Los **horarios** son la plantilla diaria de cada ruta; con ellos se generan los viajes de los próximos 7 días.
- La **auditoría** guarda quién inició sesión, vendió, anuló o modificó datos.

## Reglas que protege la base de datos

| Regla | Cómo |
|-------|------|
| No vender dos veces el mismo asiento | Índice único `ux_boletos_asiento_activo (viaje_id, asiento)` para boletos no anulados |
| El asiento debe existir en el bus | Trigger `trg_boletos_validar` |
| No vender en viajes que ya salieron o se cancelaron | Trigger `trg_boletos_validar` |
| No reducir la capacidad de un bus por debajo de asientos vendidos | Trigger `trg_buses_capacidad` |
| No borrar buses, rutas, conductores o pasajeros con historial | `FOREIGN KEY ... ON DELETE RESTRICT` |
| Un bus no puede tener dos viajes a la misma hora | `UNIQUE (bus_id, fecha, hora_salida)` |
| Placas, DNI, licencias y usuarios únicos | Restricciones `UNIQUE` |
| Valores válidos (rol, estado, método de pago, capacidad…) | Restricciones `CHECK` |

## Vistas

- `v_viajes`: cada viaje con su ruta, bus, conductor, vendidos, reservados y **asientos libres**.
- `v_boletos`: cada boleto con pasajero, ruta, bus y vendedor (para tickets e informes).
