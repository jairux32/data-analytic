"""
Modelo de Log de Sincronización para registrar operaciones de KoboToolbox.

Almacena el historial de sincronizaciones con la API de KoboToolbox
o importaciones manuales de archivos CSV/Excel.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SyncLog(Base):
    """
    Modelo para registrar sincronizaciones con KoboToolbox.

    Registra tanto sincronizaciones automáticas vía API como
    importaciones manuales de archivos.
    """
    __tablename__ = "sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sync_type: Mapped[str] = mapped_column(String(50), nullable=False)  # api, upload
    asset_uid: Mapped[Optional[str]] = mapped_column(String(255))
    source_file: Mapped[Optional[str]] = mapped_column(String(255))  # nombre del archivo si es upload
    records_synced: Mapped[int] = mapped_column(Integer, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="running")  # running, success, failed
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[Optional[int]] = mapped_column(Integer)  # usuario que inició la sincronización

    def __repr__(self) -> str:
        return f"<SyncLog(id={self.id}, type={self.sync_type}, status={self.status})>"
