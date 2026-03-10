"""
API de KoboToolbox para sincronización e importación de datos.

Endpoints para:
- Sincronización con API de KoboToolbox
- Importación manual de archivos CSV/Excel
- Gestión de mapeos de campos
- Estado de sincronizaciones
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.survey import Survey
from app.models.field_mapping import FieldMapping, DEFAULT_MAPPINGS
from app.models.sync_log import SyncLog
from app.schemas.kobo import (
    FieldMappingCreate,
    FieldMappingUpdate,
    FieldMappingResponse,
    SyncRequest,
    SyncStatusResponse,
    SyncResponse,
    UploadResponse,
    KoboConfigResponse,
    KoboConfigUpdate,
)
from app.schemas.auth import MessageResponse
from app.services.kobo_service import KoboService
from app.core.config import settings

router = APIRouter(prefix="/api/kobo", tags=["kobotoolbox"])


# === Endpoints de sincronización ===

@router.post("/sync", response_model=SyncResponse)
def sync_from_kobo(
    request: SyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("importar_datos"))
):
    """
    Sincroniza datos desde la API de KoboToolbox.

    Descarga los datos del formulario configurado y los importa a la base de datos.
    """
    if not settings.kobo_api_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de API de KoboToolbox no configurado",
        )

    # Determinar qué asset UID usar
    asset_uids = [request.asset_uid] if request.asset_uid else settings.kobo_asset_list
    if not asset_uids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay asset UIDs configurados",
        )

    # Crear registro de sincronización
    sync_log = SyncLog(
        sync_type="api",
        asset_uid=request.asset_uid or ", ".join(asset_uids),
        status="running",
        created_by=current_user.id,
    )
    db.add(sync_log)
    db.commit()
    db.refresh(sync_log)

    try:
        # Obtener mapeos de campos
        mappings = db.query(FieldMapping).filter(FieldMapping.is_active == True).all()
        mapping_dict = {m.kobo_field_name: m.internal_field_name for m in mappings}

        # Realizar sincronización
        kobo_service = KoboService(db)
        result = kobo_service.sync_from_api(
            asset_uids=asset_uids,
            api_token=settings.kobo_api_token,
            instance_url=settings.kobo_instance_url,
            mappings=mapping_dict,
        )

        # Actualizar registro de sincronización
        sync_log.records_synced = result["imported"]
        sync_log.records_skipped = result["skipped"]
        sync_log.status = "success"
        sync_log.completed_at = datetime.utcnow()

    except Exception as e:
        sync_log.status = "failed"
        sync_log.errors = str(e)
        sync_log.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en sincronización: {str(e)}",
        )

    db.commit()
    return SyncResponse(
        message=f"Sincronización completada: {result['imported']} importados, {result['skipped']} omitidos",
        sync_log=SyncStatusResponse.model_validate(sync_log),
    )


@router.post("/upload", response_model=UploadResponse)
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("importar_datos"))
):
    """
    Importa datos desde archivo CSV o Excel.

    Acepta archivos .csv o .xlsx exportados desde KoboToolbox.
    """
    # Validar tipo de archivo
    filename = file.filename if file.filename else ""
    if not filename.endswith((".csv", ".xlsx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no válido. Use .csv o .xlsx",
        )

    # Crear registro de sincronización
    sync_log = SyncLog(
        sync_type="upload",
        source_file=file.filename,
        status="running",
        created_by=current_user.id,
    )
    db.add(sync_log)
    db.commit()
    db.refresh(sync_log)

    try:
        # Obtener mapeos de campos
        mappings = db.query(FieldMapping).filter(FieldMapping.is_active == True).all()
        mapping_dict = {m.kobo_field_name: m.internal_field_name for m in mappings}

        # Procesar archivo
        kobo_service = KoboService(db)
        result = kobo_service.import_from_file(
            file=file.file,
            filename=file.filename,
            mappings=mapping_dict,
        )

        # Actualizar registro
        sync_log.records_synced = result["imported"]
        sync_log.records_skipped = result["skipped"]
        sync_log.status = "success"
        sync_log.completed_at = datetime.utcnow()

    except Exception as e:
        sync_log.status = "failed"
        sync_log.errors = str(e)
        sync_log.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en importación: {str(e)}",
        )

    db.commit()
    return UploadResponse(
        message=f"Importación completada: {result['imported']} registros importados",
        filename=file.filename,
        records_processed=result["processed"],
        records_imported=result["imported"],
        records_skipped=result["skipped"],
    )


@router.get("/status", response_model=list[SyncStatusResponse])
def get_sync_status(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el estado de las últimas sincronizaciones.
    """
    logs = db.query(SyncLog).order_by(SyncLog.started_at.desc()).limit(limit).all()
    return logs


# === Endpoints de mapeos de campos ===

@router.get("/mappings", response_model=list[FieldMappingResponse])
def get_mappings(
    category: str = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los mapeos de campos configurados.

    Permite filtrar por categoría o solo activos.
    """
    query = db.query(FieldMapping)

    if category:
        query = query.filter(FieldMapping.category == category)
    if active_only:
        query = query.filter(FieldMapping.is_active == True)

    return query.order_by(FieldMapping.category, FieldMapping.kobo_field_name).all()


@router.post("/mappings", response_model=FieldMappingResponse, status_code=status.HTTP_201_CREATED)
def create_mapping(
    request: FieldMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("configurar_kobo"))
):
    """
    Crea un nuevo mapeo de campo (solo admin).
    """
    # Verificar que no exista
    existing = db.query(FieldMapping).filter(
        FieldMapping.kobo_field_name == request.kobo_field_name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un mapeo para este campo de Kobo",
        )

    mapping = FieldMapping(**request.model_dump())
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


@router.put("/mappings/{mapping_id}", response_model=FieldMappingResponse)
def update_mapping(
    mapping_id: int,
    request: FieldMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("configurar_kobo"))
):
    """
    Actualiza un mapeo de campo (solo admin).
    """
    mapping = db.query(FieldMapping).filter(FieldMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapeo no encontrado",
        )

    # Actualizar campos
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(mapping, key, value)

    mapping.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(mapping)
    return mapping


@router.delete("/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("configurar_kobo"))
):
    """
    Elimina un mapeo de campo (solo admin).
    """
    mapping = db.query(FieldMapping).filter(FieldMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapeo no encontrado",
        )

    db.delete(mapping)
    db.commit()
    return None


@router.post("/mappings/seed", response_model=MessageResponse)
def seed_default_mappings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("configurar_kobo"))
):
    """
    Carga los mapeos de campos por defecto.

    Útil para inicializar la configuración.
    """
    created = 0
    for kobo_name, internal_name, field_type, category in DEFAULT_MAPPINGS:
        existing = db.query(FieldMapping).filter(
            FieldMapping.kobo_field_name == kobo_name
        ).first()
        if not existing:
            mapping = FieldMapping(
                kobo_field_name=kobo_name,
                internal_field_name=internal_name,
                field_type=field_type,
                category=category,
            )
            db.add(mapping)
            created += 1

    db.commit()
    return {"message": f"Se crearon {created} mapeos por defecto"}


# === Endpoints de configuración ===

@router.get("/config", response_model=KoboConfigResponse)
def get_kobo_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la configuración actual de KoboToolbox.
    """
    last_sync = db.query(SyncLog).filter(
        SyncLog.status == "success"
    ).order_by(SyncLog.completed_at.desc()).first()

    return KoboConfigResponse(
        instance_url=settings.kobo_instance_url,
        api_token_configured=bool(settings.kobo_api_token),
        asset_uids=settings.kobo_asset_list,
        sync_interval_hours=settings.kobo_sync_interval_hours,
        last_sync=last_sync.completed_at if last_sync else None,
    )


@router.put("/config", response_model=KoboConfigResponse)
def update_kobo_config(
    request: KoboConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("configurar_kobo"))
):
    """
    Actualiza la configuración de KoboToolbox (solo admin).
    """
    # Esta implementación requeriría actualizar las settings
    # Por ahora solo retornamos la configuración actual
    return get_kobo_config(db, current_user)


@router.get("/sync/history")
def get_sync_history(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el historial de sincronizaciones recientes.
    """
    syncs = db.query(SyncLog).order_by(
        SyncLog.started_at.desc()
    ).limit(limit).all()
    
    return {
        "items": [
            {
                "id": s.id,
                "sync_type": s.sync_type,
                "status": s.status,
                "records_synced": s.records_synced,
                "records_skipped": s.records_skipped,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "errors": s.errors,
            }
            for s in syncs
        ]
    }
