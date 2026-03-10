"""
API de Datos para acceso a encuestas.

Endpoints para obtener y manipular datos de encuestas:
- Lista paginada
- Detalle de registro
- Eliminación (solo admin)
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.survey import Survey
from app.schemas.survey import SurveyResponse, SurveyListResponse

router = APIRouter(prefix="/api/data", tags=["datos"])


@router.get("/surveys", response_model=SurveyListResponse)
def get_surveys(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    province: Optional[str] = Query(None),
    canton: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene lista paginada de encuestas.

    Permite filtrar por provincia, cantón, género y búsqueda por nombre.
    """
    query = db.query(Survey)

    # Aplicar filtros
    if province:
        query = query.filter(Survey.province == province)
    if canton:
        query = query.filter(Survey.canton == canton)
    if gender:
        query = query.filter(Survey.gender == gender)
    if search:
        query = query.filter(Survey.producer_name.ilike(f"%{search}%"))

    # Contar total antes de paginar
    total = query.count()

    # Ordenar
    sort_by_safe = sort_by if sort_by else "created_at"
    sort_column = getattr(Survey, sort_by_safe, Survey.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Paginar
    offset_val = (page - 1) * per_page
    surveys = query.offset(offset_val).limit(per_page).all()

    return SurveyListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=[SurveyResponse.model_validate(s) for s in surveys],
    )


@router.get("/surveys/{survey_id}", response_model=SurveyResponse)
def get_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el detalle de una encuesta específica.
    """
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )
    return survey


@router.delete("/surveys/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("eliminar_registros"))
):
    """
    Elimina una encuesta (solo admin).
    """
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    db.delete(survey)
    db.commit()
    return None


@router.get("/filters")
def get_filter_options(
    province: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene las opciones disponibles para filtros.

    Retorna listas de valores únicos para provincia, cantón, etc.
    Si se pasa province, retorna solo los cantones de esa provincia.
    """
    from sqlalchemy import func

    if province:
        cantons = db.query(Survey.canton).distinct().filter(
            Survey.canton.isnot(None),
            Survey.province == province
        ).all()
        return {
            "cantons": [c[0] for c in cantons if c[0]],
        }

    provinces = db.query(Survey.province).distinct().filter(
        Survey.province.isnot(None)
    ).all()
    cantons = db.query(Survey.canton).distinct().filter(
        Survey.canton.isnot(None)
    ).all()
    genders = db.query(Survey.gender).distinct().filter(
        Survey.gender.isnot(None)
    ).all()

    return {
        "provinces": [p[0] for p in provinces if p[0]],
        "cantons": [c[0] for c in cantons if c[0]],
        "genders": [g[0] for g in genders if g[0]],
    }
