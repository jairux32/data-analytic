"""
Modelo de Auditoría para registrar acciones de usuarios.

Registra todas las acciones importantes realizadas en el sistema
para auditoría y seguimiento.
"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """
    Modelo para registrar acciones de usuarios en el sistema.

    Attributes:
        id: Identificador único
        user_id: ID del usuario que realizó la acción
        action: Tipo de acción (login, create, update, delete, sync, export, etc.)
        entity_type: Tipo de entidad afectada (user, survey, mapping, etc.)
        entity_id: ID de la entidad afectada
        details: Detalles adicionales en JSON
        ip_address: Dirección IP del cliente
        user_agent: User agent del navegador
        created_at: Fecha y hora de la acción
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action}, created_at={self.created_at})>"
