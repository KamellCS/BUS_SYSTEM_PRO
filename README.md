# BUS SYSTEM PRO v3.0

Sistema de escritorio para una empresa de buses interprovinciales: **venta de pasajes con mapa de asientos**, gestión de flota, rutas, horarios, conductores, pasajeros, informes y usuarios.

Hecho en **Python + Tkinter** con base de datos **SQLite** (todas las tablas relacionadas con claves foráneas). No necesita instalar nada aparte de Python.

---

## 1. Cómo abrirlo en Visual Studio (el morado)

1. Descomprime el ZIP en una carpeta, por ejemplo `C:\Proyectos\BUS_SYSTEM_PRO`.
2. Haz **doble clic en `BUS_SYSTEM_PRO.sln`** (se abre en Visual Studio).
   - Si Visual Studio pide instalar la carga de trabajo **"Desarrollo de Python"**, acéptalo (Visual Studio Installer → Modificar → *Python development*).
3. Presiona **F5** (o el botón verde ▶ *Iniciar*). `main.py` ya está configurado como archivo de inicio.

**Alternativa sin .sln:** *Archivo → Abrir → Carpeta…* → elige la carpeta → clic derecho sobre `main.py` → *Establecer como elemento de inicio* → F5.

**Desde la terminal:**

```bash
cd BUS_SYSTEM_PRO
python main.py
```

> Requisito: Python **3.10 o superior** (Tkinter y SQLite ya vienen incluidos).

---

## 2. Cuentas de prueba

| Pestaña en el login | Usuario    | Contraseña    | Nombre        |
|---------------------|------------|---------------|---------------|
| Administrador       | `admin`    | `admin123`    | Carlos Gómez  |
| Trabajador          | `vendedor` | `vendedor123` | Lucía Ramos   |
| Trabajador          | `jparedes` | `vendedor123` | Jorge Paredes |

En la pantalla de login puedes hacer clic en las cuentas de prueba para autocompletar.

---

## 3. Qué puede hacer cada rol

| Módulo                                   | Administrador | Trabajador |
|------------------------------------------|:-------------:|:----------:|
| Tablero principal                        | ✔             | ✔          |
| Venta de pasajes / reservas              | ✔             | ✔          |
| Mapa de asientos y confirmar reservas    | ✔             | ✔          |
| Anular una **reserva**                   | ✔             | ✔          |
| Anular un boleto **pagado**              | ✔             | ✘          |
| Registro de pasajeros (crear / editar)   | ✔             | ✔          |
| Eliminar pasajeros                       | ✔             | ✘          |
| Rutas y horarios                         | ✔ editar      | 👁 solo ver |
| Gestión de buses, conductores            | ✔             | ✘ (no aparece en el menú) |
| Informes y exportar CSV                  | ✔             | ✘          |
| Usuarios y actividad (auditoría)         | ✔             | ✘          |
| Configuración: cambiar mi contraseña     | ✔             | ✔          |
| Configuración: empresa y respaldo de BD  | ✔             | ✘          |

Los permisos se validan **dos veces**: el menú oculta lo que no corresponde y además cada servicio verifica el rol (`session.requiere_admin()`).

---

## 4. Funcionalidades

- **Login** con pestañas Administrador / Trabajador, contraseñas cifradas (PBKDF2‑SHA256 con sal), bloqueo de 30 s tras 5 intentos fallidos y registro de cada acceso.
- **Tablero**: viajes de hoy, pasajeros, ventas del día, ocupación, mapa de la unidad, próximas salidas con botones *Ver detalles* y *Vender*, últimas ventas.
- **Venta de pasajes** en 3 pasos: viaje → asiento en el mapa → datos del pasajero. Si el DNI ya existe, autocompleta. Emite un **boleto electrónico** (se puede guardar como .txt).
- **Mapa de asientos**: disponible / ocupado / reservado, detalle del pasajero, confirmar pago de reservas y anular boletos.
- **Rutas y horarios**: los horarios fijos generan automáticamente los viajes de los próximos 7 días. Viajes extra y cancelación (anula sus boletos).
- **Buses y conductores**: CRUD completo con estados (operativo, mantenimiento, fuera de servicio).
- **Informes**: ingresos, boletos, ticket promedio, gráfico de ingresos por día, ranking por ruta, por vendedor y por método de pago. Exporta a CSV (abre en Excel).
- **Usuarios**: crear trabajadores o administradores, restablecer contraseñas, activar/desactivar y ver la auditoría.
- **Configuración**: cambiar contraseña, datos de la empresa y **respaldo de la base de datos**.

---

## 5. Base de datos

- Archivo: `data/bus_system.db` (se crea solo la primera vez con datos de demostración).
- Esquema completo: [`database/schema.sql`](database/schema.sql)
- Diagrama entidad–relación y explicación: [`database/DIAGRAMA_BD.md`](database/DIAGRAMA_BD.md)
- Consultas de ejemplo para presentar: [`database/consultas_utiles.sql`](database/consultas_utiles.sql)

Para ver las tablas puedes usar **DB Browser for SQLite** (gratis) y abrir `data/bus_system.db`.

Para **reiniciar** los datos de demostración: cierra el programa y borra `data/bus_system.db`.

---

## 6. Estructura del proyecto

```
BUS_SYSTEM_PRO/
├── main.py                    ← punto de entrada (F5)
├── BUS_SYSTEM_PRO.sln         ← abrir con Visual Studio
├── BUS_SYSTEM_PRO.pyproj
├── database/
│   ├── schema.sql             ← tablas, claves foráneas, triggers y vistas
│   ├── DIAGRAMA_BD.md
│   └── consultas_utiles.sql
├── data/                      ← aquí se crea la base de datos y los respaldos
└── app/
    ├── config.py              ← rutas y constantes
    ├── db.py                  ← conexión SQLite y transacciones
    ├── seed.py                ← datos de demostración
    ├── security.py            ← cifrado de contraseñas
    ├── session.py             ← usuario conectado y permisos
    ├── errors.py              ← errores de negocio y traducción de errores SQL
    ├── utils.py               ← validaciones (cadenas/regex), formatos y recursividad
    ├── services/              ← LÓGICA DE NEGOCIO (sin interfaz)
    │   ├── auth.py            ← login / logout
    │   ├── ventas.py          ← pasajeros y boletos
    │   ├── viajes.py          ← programación y ocupación
    │   ├── catalogos.py       ← buses, conductores, rutas, horarios
    │   ├── usuarios.py
    │   ├── informes.py
    │   ├── configuracion.py
    │   └── auditoria.py
    └── ui/                    ← INTERFAZ (Tkinter)
        ├── app.py             ← ventana raíz: login ↔ sistema
        ├── login.py
        ├── shell.py           ← barra lateral + barra superior
        ├── theme.py           ← colores y tipografía
        ├── icons.py           ← íconos y bus dibujados en Canvas
        ├── widgets.py         ← botones, tarjetas, tablas, mapa de asientos, gráfico
        ├── ticket.py          ← boleto electrónico
        └── views/             ← una pantalla por archivo
```

Arquitectura en capas: **UI → Servicios → Base de datos**. La interfaz nunca escribe SQL; todo pasa por `services/`.

---

## 7. Temas del curso que se aplican

| Tema                    | Dónde verlo |
|-------------------------|-------------|
| Funciones y modularidad | Paquetes `services/` y `ui/views/`, una responsabilidad por módulo |
| Arreglos / listas       | Listas de viajes, asientos (`SeatMap`), resultados de consultas, `merge_sort` |
| Cadenas                 | `utils.py`: validación con expresiones regulares de DNI, placa, teléfono, correo, hora; normalización de nombres; código del boleto |
| Persistencia            | SQLite (`db.py`, `schema.sql`), respaldo de BD, exportación CSV, boleto .txt |
| Recursividad            | `utils.merge_sort` (usado en Informes) y `utils.busqueda_binaria` |
| Control de versiones    | `.gitignore` incluido; la BD no se versiona |

---

## 8. Problemas comunes

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'app'` | Ejecuta `main.py` desde la carpeta del proyecto (en VS, usa el `.sln`). |
| `No module named 'tkinter'` | Reinstala Python desde python.org marcando **tcl/tk and IDLE**. |
| Error de sintaxis con `str \| None` | Tu Python es anterior a 3.10. Instala 3.10 o superior. |
| Quiero empezar con datos limpios | Borra `data/bus_system.db` y vuelve a ejecutar. |
| Algo falló inesperadamente | Revisa `data/errores.log`. |
