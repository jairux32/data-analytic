"""
Modelo de Usuario para autenticación y autorización.

Define la estructura de la tabla de usuarios con campos para:
- Autenticación (email, password_hash)
- Perfil (full_name, role, zone)
- Estado (is_active, created_at, updated_at)
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """
    Modelo de usuario para autenticación y autorización.

    Attributes:
        id: Identificador único del usuario
        email: Correo electrónico único del usuario
        password_hash: Hash de la contraseña
        full_name: Nombre completo del usuario
        role: Rol del usuario (admin, editor, visor, analista, supervisor, técnico)
        zone: Zona geográfica asignada (guayas, los_rios, todas)
        is_active: Indica si el usuario está activo
        last_login: Última fecha de inicio de sesión
        created_at: Fecha de creación del registro
        updated_at: Fecha de última modificación
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="visor", nullable=False)
    zone: Mapped[str] = mapped_column(String(50), default="todas", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role}, zone={self.zone})>"
