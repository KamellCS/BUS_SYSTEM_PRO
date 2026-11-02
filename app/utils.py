"""Utilidades: validación de cadenas, formatos y algoritmos (recursividad)."""
import re
import secrets
from datetime import date, datetime

from .errors import AppError
from . import config

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

# --------------------------------------------------------------------- cadenas
_DOC_REGEX = {
    "DNI": (r"\d{8}", "El DNI debe tener 8 dígitos"),
    "CE": (r"[A-Z0-9]{9,12}", "El carné de extranjería debe tener de 9 a 12 caracteres"),
    "PASAPORTE": (r"[A-Z0-9]{6,12}", "El pasaporte debe tener de 6 a 12 letras o números"),
}


def normalizar_nombre(texto: str) -> str:
    """'  juan   CARLOS ' -> 'Juan Carlos'"""
    return " ".join(p.capitalize() for p in texto.split())


def validar_nombre(texto: str, campo: str) -> str:
    texto = normalizar_nombre(texto)
    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]{2,60}", texto):
        raise AppError(f"{campo}: usa solo letras (2 a 60 caracteres)")
    return texto


def validar_documento(tipo: str, numero: str) -> str:
    if tipo not in _DOC_REGEX:
        raise AppError("Selecciona un tipo de documento")
    numero = numero.strip().upper()
    patron, mensaje = _DOC_REGEX[tipo]
    if not re.fullmatch(patron, numero):
        raise AppError(mensaje)
    return numero


def validar_dni(numero: str) -> str:
    return validar_documento("DNI", numero)


def validar_telefono(texto: str, requerido=False) -> str:
    texto = re.sub(r"[\s-]", "", texto or "")
    if not texto and not requerido:
        return ""
    if not re.fullmatch(r"9\d{8}", texto):
        raise AppError("El teléfono debe tener 9 dígitos y empezar con 9")
    return texto


def validar_email(texto: str) -> str:
    texto = (texto or "").strip().lower()
    if texto and not re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", texto):
        raise AppError("Correo electrónico inválido")
    return texto


def validar_placa(texto: str) -> str:
    texto = texto.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{3}-\d{3}", texto):
        raise AppError("La placa debe tener el formato ABC-123")
    return texto


def validar_hora(texto: str) -> str:
    texto = texto.strip()
    if re.fullmatch(r"\d:[0-5]\d", texto):
        texto = "0" + texto
    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", texto):
        raise AppError("La hora debe tener el formato HH:MM (24 horas)")
    return texto


def validar_fecha(texto: str) -> str:
    try:
        return date.fromisoformat(texto.strip()).isoformat()
    except ValueError:
        raise AppError("La fecha debe tener el formato AAAA-MM-DD") from None


def validar_password(texto: str) -> str:
    if len(texto) < 6 or not re.search(r"[A-Za-z]", texto) or not re.search(r"\d", texto):
        raise AppError("La contraseña debe tener al menos 6 caracteres, con letras y números")
    return texto


def validar_username(texto: str) -> str:
    texto = texto.strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9._]{2,19}", texto):
        raise AppError("Usuario: 3 a 20 caracteres, empieza con letra (a-z, 0-9, punto, guion bajo)")
    return texto


def a_entero(texto, campo, minimo=None, maximo=None) -> int:
    try:
        valor = int(str(texto).strip())
    except ValueError:
        raise AppError(f"{campo} debe ser un número entero") from None
    if (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo):
        raise AppError(f"{campo} debe estar entre {minimo} y {maximo}")
    return valor


def a_decimal(texto, campo, minimo=0.0) -> float:
    try:
        valor = float(str(texto).replace(",", ".").replace(config.MONEDA, "").strip())
    except ValueError:
        raise AppError(f"{campo} debe ser un número") from None
    if valor < minimo:
        raise AppError(f"{campo} debe ser mayor o igual a {minimo}")
    return round(valor, 2)


def requerido(texto, campo) -> str:
    texto = (texto or "").strip()
    if not texto:
        raise AppError(f"{campo} es obligatorio")
    return texto


# --------------------------------------------------------------------- formatos
def dinero(valor) -> str:
    return f"{config.MONEDA} {float(valor or 0):,.2f}"


def dinero_corto(valor) -> str:
    valor = float(valor or 0)
    if valor >= 1000:
        return f"{config.MONEDA} {valor / 1000:.1f}k"
    return f"{config.MONEDA} {valor:.0f}"


def fecha_larga(d: date | None = None) -> str:
    d = d or date.today()
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def fecha_corta(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{DIAS[d.weekday()]} {d.day:02d}/{d.month:02d}"


def fecha_hora(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return iso or ""


def posicion_asiento(n: int) -> str:
    return "Ventana" if (n - 1) % 4 in (0, 3) else "Pasillo"


def generar_codigo_boleto(viaje_id: int, asiento: int, cuando: datetime | None = None,
                          sufijo: str | None = None) -> str:
    cuando = cuando or datetime.now()
    sufijo = sufijo or secrets.token_hex(2).upper()
    return f"B{cuando:%y%m%d}-{viaje_id:04d}-{asiento:02d}{sufijo}"


# --------------------------------------------------------------------- recursividad
def merge_sort(items, key=lambda x: x, reverse=False):
    """Ordenamiento por mezcla (recursivo). Se usa en los informes."""
    items = list(items)
    if len(items) <= 1:                       # caso base
        return items
    medio = len(items) // 2
    izquierda = merge_sort(items[:medio], key, reverse)   # llamada recursiva
    derecha = merge_sort(items[medio:], key, reverse)     # llamada recursiva
    return _mezclar(izquierda, derecha, key, reverse)


def _mezclar(a, b, key, reverse):
    resultado, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        primero = key(a[i]) >= key(b[j]) if reverse else key(a[i]) <= key(b[j])
        if primero:
            resultado.append(a[i]); i += 1
        else:
            resultado.append(b[j]); j += 1
    resultado.extend(a[i:])
    resultado.extend(b[j:])
    return resultado


def busqueda_binaria(lista, objetivo, key=lambda x: x, inicio=0, fin=None):
    """Búsqueda binaria recursiva sobre una lista ordenada. Devuelve índice o -1."""
    if fin is None:
        fin = len(lista) - 1
    if inicio > fin:                          # caso base: no encontrado
        return -1
    medio = (inicio + fin) // 2
    valor = key(lista[medio])
    if valor == objetivo:
        return medio
    if objetivo < valor:
        return busqueda_binaria(lista, objetivo, key, inicio, medio - 1)
    return busqueda_binaria(lista, objetivo, key, medio + 1, fin)
