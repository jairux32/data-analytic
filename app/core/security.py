"""
Módulo de seguridad: JWT, hashing de contraseñas y.

Este módulo proporciona las funciones necesarias para:
- Crear dependencias de autenticación y verificar tokens JWT
- Hashear y verificar contraseñas
- Dependencias de FastAPI para autenticación y autorización
- Sistema de roles y permisos granulares
- Registro de auditoría
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog

# Contexto para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
http_bearer = HTTPBearer(auto_error=False)
httpBearer = HTTPBearer(auto_error=False)

# === Definición de Roles y Permisos ===

# Roles disponibles en el sistema
ROLES = ["admin", "editor", "visor", "analista", "supervisor", "tecnico"]

# Zonas geográficas disponibles
ZONES = ["todas", "guayas", "los_rios"]

# Permisos del sistema
PERMISSIONS = {
    # Permisos de gestión de usuarios
    "gestionar_usuarios": "Crear, editar, eliminar usuarios",
    "ver_usuarios": "Ver lista de usuarios",

    # Permisos de configuración Kobo
    "configurar_kobo": "Configurar conexión con KoboToolbox",
    "gestionar_mapeos": "Gestionar mapeos de campos",
    "gestionar_sincronizacion": "Iniciar y configurar sincronización",

    # Permisos de datos
    "importar_datos": "Importar datos desde CSV/Excel",
    "exportar_reportes": "Exportar datos a PDF/Excel",
    "eliminar_registros": "Eliminar registros de encuestas",
    "editar_survey": "Editar datos de encuestas",

    # Permisos de visualización
    "ver_dashboard": "Ver dashboard y KPIs",
    "ver_mapas": "Ver mapas geoespaciales",
    "filtrar_tablas": "Filtrar y buscar en tablas de datos",

    # Permisos de análisis
    "ver_analisis": "Ver análisis y estadísticas avanzadas",
    "crear_reportes": "Crear reportes personalizados",
}

# Definición de permisos por rol
ROLE_PERMISSIONS = {
    "admin": [
        "gestionar_usuarios", "ver_usuarios", "configurar_kobo",
        "gestionar_mapeos", "gestionar_sincronizacion", "importar_datos",
        "exportar_reportes", "eliminar_registros", "editar_survey",
        "ver_dashboard", "ver_mapas", "filtrar_tablas", "ver_analisis",
        "crear_reportes"
    ],
    "editor": [
        "importar_datos", "exportar_reportes", "editar_survey",
        "ver_dashboard", "ver_mapas", "filtrar_tablas", "ver_analisis",
        "crear_reportes"
    ],
    "visor": [
        "ver_dashboard", "ver_mapas", "filtrar_tablas", "exportar_reportes"
    ],
    "analista": [
        "ver_dashboard", "ver_mapas", "filtrar_tablas", "exportar_reportes",
        "ver_analisis", "crear_reportes"
    ],
    "supervisor": [
        "importar_datos", "exportar_reportes", "editar_survey",
        "ver_dashboard", "ver_mapas", "filtrar_tablas", "ver_analisis",
        "gestionar_sincronizacion"
    ],
    "tecnico": [
        "ver_dashboard", "ver_mapas", "filtrar_tablas", "exportar_reportes"
    ],
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña."""
    return pwd_context.hash(password[:72])


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token de acceso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Crea un token de refresco JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decodifica un token JWT."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Obtiene el usuario actual a partir del token JWT (desde cookie o header)."""
    token = None

    # Buscar en cookie primero
    token = request.cookies.get("access_token")

    # Si no está en cookie, buscar en header Authorization manualmente
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido",
        )
    user_id = int(str(user_id_raw))
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    return user


def require_role(allowed_roles: list[str]):
    """Dependencia de FastAPI para verificar roles."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Roles permitidos: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


def has_permission(role: str, permission: str) -> bool:
    """Verifica si un rol tiene un permiso específico."""
    return permission in ROLE_PERMISSIONS.get(role, [])


def get_user_permissions(role: str) -> list[str]:
    """Obtiene la lista de permisos de un rol."""
    return ROLE_PERMISSIONS.get(role, [])


def require_permission(permission: str):
    """Dependencia de FastAPI para verificar permisos específicos."""
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso requerido: {permission}"
            )
        return current_user

    return permission_checker


def require_zone(allowed_zones: list[str]):
    """Dependencia de FastAPI para verificar zona geográfica."""
    def zone_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.zone not in allowed_zones and current_user.zone != "todas":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Zonas permitidas: {', '.join(allowed_zones)}"
            )
        return current_user

    return zone_checker


def get_user_zone_filter(role: str, zone: str) -> Optional[dict]:
    """Obtiene el filtro de zona para consultas de base de datos."""
    if zone == "todas":
        return None
    return {"province": zone.capitalize()}


# === Funciones de Auditoría ===

def log_audit(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    details: Optional[str] = None,
    request: Optional[Request] = None
):
    """Registra una acción en el log de auditoría."""
    ip_address = None
    user_agent = None

    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:500] if request.headers else None

    audit = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit)
    db.commit()
