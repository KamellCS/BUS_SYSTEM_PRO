"""Contraseñas: nunca se guardan en texto plano.

Se usa PBKDF2-HMAC-SHA256 con una "sal" aleatoria por usuario.
"""
import hashlib
import hmac
import secrets

ITERACIONES = 120_000


def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt_hex = salt_hex or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                 bytes.fromhex(salt_hex), ITERACIONES)
    return digest.hex(), salt_hex


def verificar_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    calculado, _ = hash_password(password, salt_hex)
    return hmac.compare_digest(calculado, hash_hex)
