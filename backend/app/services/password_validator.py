"""Shared password strength validation (Q6 — DRY)."""

import re

_SYMBOL_REGEX = re.compile(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/\\`~]')

def validate_password_strength(v: str, *, lang: str = "es") -> str:
    msgs = {
        "es": {
            "length": "La contraseña debe tener al menos 8 caracteres",
            "upper": "La contraseña debe contener al menos una mayúscula",
            "digit": "La contraseña debe contener al menos un número",
            "symbol": "La contraseña debe contener al menos un símbolo especial",
        },
        "en": {
            "length": "Password must be at least 8 characters",
            "upper": "Password must contain at least one uppercase letter",
            "digit": "Password must contain at least one number",
            "symbol": "Password must contain at least one special character",
        },
    }
    m = msgs[lang]
    if len(v) < 8:
        raise ValueError(m["length"])
    if not re.search(r'[A-Z]', v):
        raise ValueError(m["upper"])
    if not re.search(r'[0-9]', v):
        raise ValueError(m["digit"])
    if not _SYMBOL_REGEX.search(v):
        raise ValueError(m["symbol"])
    return v
