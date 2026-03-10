"""
Schemas Pydantic para KoboToolbox y mapeos de campos.

Define los esquemas para sincronización, importación y configuración
de mapeos entre KoboToolbox y la aplicación.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# === Schemas para Mapeos de Campos ===

class FieldMappingBase(BaseModel):
    """Schema base para mapeo de campos."""
    kobo_field_name: str
    internal_field_name: str
    field_type: str = Field(..., pattern="^(string|number|date|select_one|select_multiple)$")
    category: str = Field(..., pattern="^(socioeconomic|agronomic|environmental|governance|geospatial)$")
    is_active: bool = True
    description: Optional[str] = None
    default_value: Optional[str] = None


class FieldMappingCreate(FieldMappingBase):
    """Schema para crear mapeo de campo."""
    pass


class FieldMappingUpdate(BaseModel):
    """Schema para actualizar mapeo de campo."""
    kobo_field_name: Optional[str] = None
    internal_field_name: Optional[str] = None
    field_type: Optional[str] = Field(None, pattern="^(string|number|date|select_one|select_multiple)$")
    category: Optional[str] = Field(None, pattern="^(socioeconomic|agronomic|environmental|governance|geospatial)$")
    is_active: Optional[bool] = None
    description: Optional[str] = None
    default_value: Optional[str] = None


class FieldMappingResponse(FieldMappingBase):
    """Schema para respuesta de mapeo de campo."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Schemas para Sincronización ===

class SyncRequest(BaseModel):
    """Schema para solicitar sincronización con KoboToolbox."""
    asset_uid: Optional[str] = None  # si no se especifica, usa todos los configurados


class SyncStatusResponse(BaseModel):
    """Schema para estado de sincronización."""
    id: int
    sync_type: str
    asset_uid: Optional[str] = None
    source_file: Optional[str] = None
    records_synced: int
    records_skipped: int
    errors: Optional[str] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SyncResponse(BaseModel):
    """Schema para respuesta de sincronización."""
    message: str
    sync_log: SyncStatusResponse


# === Schemas para Importación de Archivos ===

class UploadResponse(BaseModel):
    """Schema para respuesta de importación de archivo."""
    message: str
    filename: str
    records_processed: int
    records_imported: int
    records_skipped: int


# === Schemas para Configuración ===

class KoboConfigResponse(BaseModel):
    """Schema para configuración actual de KoboToolbox."""
    instance_url: str
    api_token_configured: bool
    asset_uids: list[str]
    sync_interval_hours: int
    last_sync: Optional[datetime] = None


class KoboConfigUpdate(BaseModel):
    """Schema para actualizar configuración de KoboToolbox."""
    instance_url: Optional[str] = None
    api_token: Optional[str] = None
    asset_uids: Optional[str] = None
    sync_interval_hours: Optional[int] = Field(None, ge=0)
