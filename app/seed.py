"""Datos de demostración. Se cargan solo la primera vez (base de datos vacía)."""
import random
from datetime import date, datetime, time, timedelta

from . import config, db, utils
from .security import hash_password

USUARIOS = [
    # usuario, contraseña, nombres, apellidos, rol
    ("admin", "admin123", "Carlos", "Gómez", "admin"),
    ("vendedor", "vendedor123", "Lucía", "Ramos", "trabajador"),
    ("jparedes", "vendedor123", "Jorge", "Paredes", "trabajador"),
]

BUSES = [
    # unidad, placa, marca, modelo, año, capacidad, estado
    ("45B", "ABC-123", "Mercedes-Benz", "O500 RSD", 2022, 44, "operativo"),
    ("458", "DEF-456", "Scania", "K410 Irizar i6", 2021, 40, "operativo"),
    ("512", "GHI-789", "Volvo", "B450R", 2023, 48, "operativo"),
    ("620", "JKL-012", "Mercedes-Benz", "O500 RS", 2020, 36, "operativo"),
    ("733", "PQR-678", "Scania", "K360 Marcopolo", 2022, 44, "operativo"),
    ("701", "MNO-345", "Yutong", "ZK6122H9", 2019, 44, "mantenimiento"),
]

CONDUCTORES = [
    ("40512345", "Roberto", "Acosta Mendoza", "Q40512345", "987111222"),
    ("41234567", "Pedro", "Gonzales Rivera", "Q41234567", "987111223"),
    ("42345678", "Miguel", "Quispe Santander", "Q42345678", "987111224"),
    ("43456789", "Víctor", "Huamán Torres", "Q43456789", "987111225"),
    ("44567890", "José", "Mendoza Castillo", "Q44567890", "987111226"),
    ("45678901", "Raúl", "Chávez Rojas", "Q45678901", "987111227"),
]

RUTAS = [
    # código, origen, destino, km, minutos, precio
    ("R01", "Lima", "Ica", 303, 300, 45.0),
    ("R02", "Lima", "Huacho", 148, 150, 30.0),
    ("R03", "Lima", "Nazca", 450, 450, 70.0),
    ("R04", "Lima", "Arequipa", 1010, 960, 120.0),
    ("R05", "Lima", "Trujillo", 560, 540, 80.0),
    ("R06", "Lima", "Huancayo", 300, 420, 60.0),
]

HORARIOS = [
    # código ruta, hora, unidad bus, índice conductor
    ("R01", "06:30", "45B", 0), ("R01", "13:00", "458", 1), ("R01", "19:30", "45B", 0),
    ("R02", "08:00", "620", 2), ("R02", "15:30", "620", 2),
    ("R03", "09:00", "512", 3), ("R03", "22:00", "512", 3),
    ("R04", "17:00", "733", 4),
    ("R05", "21:00", "458", 1),
    ("R06", "10:00", "733", 5), ("R06", "23:00", "620", 5),
]

NOMBRES = ["Juan", "María", "Carlos", "Ana", "Luis", "Rosa", "José", "Carmen", "Miguel", "Lucía",
           "Jorge", "Patricia", "Diego", "Sofía", "Andrés", "Valeria", "Fernando", "Gabriela",
           "Ricardo", "Daniela", "Alejandro", "Camila", "Martín", "Fiorella", "Renzo", "Milagros",
           "Hugo", "Paola", "César", "Elena", "Kevin", "Brenda", "Óscar", "Lorena", "Iván", "Nataly"]
APELLIDOS = ["García", "Rodríguez", "Quispe", "Flores", "Sánchez", "Ramírez", "Torres", "Díaz",
             "Mendoza", "Rojas", "Vargas", "Castillo", "Huamán", "Chávez", "Gutiérrez", "Ramos",
             "Paredes", "Salazar", "Cruz", "Morales", "Ortiz", "Vásquez", "Silva", "Reyes",
             "Espinoza", "Herrera", "Campos", "Aguilar", "Medina", "Palacios", "Ccori", "Mamani"]
EXTRANJEROS = [("PASAPORTE", "Jennifer", "Smith"), ("PASAPORTE", "Laurent", "Dupont"),
               ("CE", "Andrea", "Pérez"), ("CE", "Mateo", "Bolívar"),
               ("PASAPORTE", "Lukas", "Müller"), ("CE", "Valentina", "Ríos")]


def seed():
    rng = random.Random(2026)
    c = db.conn()
    with db.transaction() as c:
        # ---- usuarios
        for username, pwd, nom, ape, rol in USUARIOS:
            h, salt = hash_password(pwd)
            c.execute("""INSERT INTO usuarios (username, password_hash, salt, nombres, apellidos, rol)
                         VALUES (?,?,?,?,?,?)""", (username, h, salt, nom, ape, rol))
        c.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('empresa_nombre', ?)",
                  (config.EMPRESA_DEFAULT,))

        # ---- catálogos
        c.executemany("""INSERT INTO buses (unidad, placa, marca, modelo, anio, capacidad, estado)
                         VALUES (?,?,?,?,?,?,?)""", BUSES)
        c.executemany("""INSERT INTO conductores (dni, nombres, apellidos, licencia, telefono)
                         VALUES (?,?,?,?,?)""", CONDUCTORES)
        c.executemany("""INSERT INTO rutas (codigo, origen, destino, distancia_km, duracion_min, precio_base)
                         VALUES (?,?,?,?,?,?)""", RUTAS)
        rutas = {r["codigo"]: r["id"] for r in c.execute("SELECT id, codigo FROM rutas")}
        buses = {r["unidad"]: r["id"] for r in c.execute("SELECT id, unidad FROM buses")}
        conductores = [r["id"] for r in c.execute("SELECT id FROM conductores ORDER BY id")]
        c.executemany("INSERT INTO horarios (ruta_id, hora, bus_id, conductor_id) VALUES (?,?,?,?)",
                      [(rutas[r], h, buses[u], conductores[k]) for r, h, u, k in HORARIOS])

        # ---- pasajeros
        hoy = date.today()
        usados, pasajeros = set(), []
        while len(pasajeros) < 160:
            dni = str(rng.randint(40_000_000, 79_999_999))
            if dni in usados:
                continue
            usados.add(dni)
            nom = rng.choice(NOMBRES)
            ape = f"{rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}"
            tel = f"9{rng.randint(10_000_000, 99_999_999)}"
            email = (f"{utils.normalizar_nombre(nom).lower()}.{ape.split()[0].lower()}{rng.randint(1, 99)}"
                     f"@gmail.com") if rng.random() < 0.7 else ""
            email = (email.replace("á", "a").replace("é", "e").replace("í", "i")
                     .replace("ó", "o").replace("ú", "u").replace("ñ", "n"))
            creado = datetime.combine(hoy - timedelta(days=rng.randint(1, 180)),
                                      time(rng.randint(7, 21), rng.randint(0, 59)))
            pasajeros.append(("DNI", dni, nom, ape, tel, email, f"{creado:%Y-%m-%d %H:%M:%S}"))
        for tipo, nom, ape in EXTRANJEROS:
            num = f"{rng.choice('ABCX')}{rng.randint(10_000_000, 99_999_999)}"
            pasajeros.append((tipo, num, nom, ape, f"9{rng.randint(10_000_000, 99_999_999)}", "",
                              f"{hoy - timedelta(days=rng.randint(1, 60))} 10:00:00"))
        c.executemany("""INSERT INTO pasajeros (tipo_doc, num_doc, nombres, apellidos, telefono, email, creado_en)
                         VALUES (?,?,?,?,?,?,?)""", pasajeros)

    # ---- viajes: 14 días atrás (historial) + próximos días
    from .services import viajes as viajes_srv
    viajes_srv.programar_desde_horarios(dias=14 + config.DIAS_A_PROGRAMAR,
                                        desde=hoy - timedelta(days=14))
    _seed_boletos(rng, hoy)


def _seed_boletos(rng: random.Random, hoy: date):
    pasajero_ids = [r[0] for r in db.conn().execute("SELECT id FROM pasajeros")]
    usuario_ids = [r[0] for r in db.conn().execute("SELECT id FROM usuarios")]
    lista = db.query("""SELECT v.id, v.fecha, v.hora_salida, v.precio, b.capacidad
                          FROM viajes v JOIN buses b ON b.id = v.bus_id""")
    ahora = datetime.now()
    filas = []
    for v in lista:
        fecha = date.fromisoformat(v["fecha"])
        dias = (fecha - hoy).days
        if dias < 0:
            ocupacion = rng.uniform(0.45, 0.95)
        elif dias == 0:
            ocupacion = rng.uniform(0.35, 0.80)
        else:
            ocupacion = max(0.05, rng.uniform(0.25, 0.60) - dias * 0.06)
        n = int(v["capacidad"] * ocupacion)
        asientos = rng.sample(range(1, v["capacidad"] + 1), n)
        clientes = rng.sample(pasajero_ids, n)
        salida = datetime.combine(fecha, time.fromisoformat(v["hora_salida"]))
        for asiento, pid in zip(asientos, clientes):
            ultimo = min(salida - timedelta(minutes=30), ahora)
            primero = salida - timedelta(days=6)
            if ultimo <= primero:
                primero, ultimo = ahora - timedelta(days=2), ahora
            emitido = primero + (ultimo - primero) * rng.random()
            estado = "reservado" if dias >= 0 and rng.random() < 0.12 else "vendido"
            metodo = rng.choice(["efectivo", "tarjeta", "yape", "yape", "plin", "transferencia"])
            codigo = utils.generar_codigo_boleto(v["id"], asiento, emitido,
                                                 f"{rng.randint(0, 255):02X}")
            filas.append((codigo, v["id"], pid, rng.choice(usuario_ids), asiento, v["precio"],
                          estado, metodo, f"{emitido:%Y-%m-%d %H:%M:%S}"))
    with db.transaction() as c:
        c.executemany("""INSERT INTO boletos (codigo, viaje_id, pasajero_id, usuario_id, asiento, precio,
                                              estado, metodo_pago, fecha_emision)
                         VALUES (?,?,?,?,?,?,?,?,?)""", filas)
        c.execute("INSERT INTO auditoria (usuario_id, accion, detalle) VALUES (NULL, 'SISTEMA', ?)",
                  (f"Base de datos creada con {len(filas)} boletos de demostración",))
