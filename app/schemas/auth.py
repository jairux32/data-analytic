"""
Schemas Pydantic para autenticación.

Define los esquemas para login, tokens JWT, usuarios, roles y permisos.
"""
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# === Schemas de Request ===

class LoginRequest(BaseModel):
    """Schema para solicitud de login."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class TokenRequest(BaseModel):
    """Schema para solicitud de refresh token."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Schema para cambio de contraseña."""
    current_password: str
    new_password: str = Field(..., min_length=6)


class UserCreateRequest(BaseModel):
    """Schema para crear nuevo usuario (solo admin)."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    role: str = Field(default="visor", pattern="^(admin|editor|visor|analista|supervisor|tecnico)$")
    zone: str = Field(default="todas", pattern="^(todas|guayas|los_rios)$")


class UserUpdateRequest(BaseModel):
    """Schema para actualizar usuario."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2)
    role: Optional[str] = Field(None, pattern="^(admin|editor|visor|analista|supervisor|tecnico)$")
    zone: Optional[str] = Field(None, pattern="^(todas|guayas|los_rios)$")
    is_active: Optional[bool] = None


class UserFilterRequest(BaseModel):
    """Schema para filtrar usuarios."""
    role: Optional[str] = None
    zone: Optional[str] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None


# === Schemas de Response ===

class TokenResponse(BaseModel):
    """Schema para respuesta de tokens JWT."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema para respuesta de datos de usuario."""
    id: int
    email: str
    full_name: str
    role: str
    zone: str
    is_active: bool
    last_login: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

    @field_validator('last_login', 'created_at', 'updated_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return v
        if v is None:
            return None
        return v.isoformat() if hasattr(v, 'isoformat') else str(v)


class UserListResponse(BaseModel):
    """Schema para lista paginada de usuarios."""
    total: int
    page: int
    per_page: int
    items: List[UserResponse]


class RoleResponse(BaseModel):
    """Schema para información de rol."""
    name: str
    description: str
    permissions: List[str]


class PermissionsResponse(BaseModel):
    """Schema para permisos del usuario."""
    role: str
    zone: str
    permissions: List[str]
    all_permissions: dict


class AuditLogResponse(BaseModel):
    """Schema para registro de auditoría."""
    id: int
    user_id: Optional[int]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema para lista de registros de auditoría."""
    total: int
    page: int
    per_page: int
    items: List[AuditLogResponse]


# === Schemas de Mensajes ===

class MessageResponse(BaseModel):
    """Schema para mensajes simples."""
    message: str


class ErrorResponse(BaseModel):
    """Schema para respuestas de error."""
    detail: str
