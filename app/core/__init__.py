"""
Paquete core de la aplicación.

Contiene la configuración central, base de datos y seguridad.
"""
from app.core.config import settings, get_settings
from app.core.database import Base, get_db, init_db, engine, SessionLocal
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_role,
    require_permission,
    ROLES,
    has_permission,
)

__all__ = [
    "settings",
    "get_settings",
    "Base",
    "get_db",
    "init_db",
    "engine",
    "SessionLocal",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user",
    "require_role",
    "require_permission",
    "ROLES",
    "has_permission",
]
