"""
API de Mapas para visualizaciones geoespaciales.

Endpoints para obtener datos de mapas:
- Puntos de encuestas
- Mapa de calor
- Datos para coropletas
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.survey import Survey

router = APIRouter(prefix="/api/maps", tags=["mapas"])


@router.get("/points")
def get_map_points(
    province: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los puntos de ubicación de las encuestas.

    Retorna coordenadas GPS y datos asociados para mostrar en el mapa.
    """
    query = db.query(Survey).filter(
        Survey.gps_latitude.isnot(None),
        Survey.gps_longitude.isnot(None)
    )

    if province:
        query = query.filter(Survey.province == province)
    if gender:
        query = query.filter(Survey.gender == gender)

    surveys = query.all()

    points = []
    for s in surveys:
        points.append({
            "id": s.id,
            "lat": s.gps_latitude,
            "lon": s.gps_longitude,
            "producer_name": s.producer_name,
            "province": s.province,
            "canton": s.canton,
            "farm_size": s.farm_size_hectares,
            "variety": s.cacao_varieties.split()[0] if s.cacao_varieties else None,
            "yield": s.yield_quintals_per_ha,
        })

    return {"points": points, "total": len(points)}


@router.get("/heatmap")
def get_heatmap_data(
    province: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene datos para el mapa de calor.

    Retorna arreglo de [lat, lon, intensidad] para heatmap.
    """
    query = db.query(Survey).filter(
        Survey.gps_latitude.isnot(None),
        Survey.gps_longitude.isnot(None)
    )

    if province:
        query = query.filter(Survey.province == province)

    surveys = query.all()

    heat_data = [[s.gps_latitude, s.gps_longitude, 1] for s in surveys]

    return {"heatmap": heat_data, "total": len(heat_data)}


@router.get("/stats/by-canton")
def get_stats_by_canton(
    province: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene estadísticas por cantón para coropletas.

    Retorna datos agregados por cantón para visualización.
    """
    from sqlalchemy import func

    query = db.query(
        Survey.canton,
        func.count(Survey.id).label("count"),
        func.avg(Survey.yield_quintals_per_ha).label("avg_yield"),
        func.avg(Survey.farm_size_hectares).label("avg_farm_size"),
    ).group_by(Survey.canton)

    if province:
        query = query.filter(Survey.province == province)

    results = query.all()

    canton_data = []
    for r in results:
        if r.canton:
            canton_data.append({
                "canton": r.canton,
                "survey_count": r.count,
                "avg_yield": float(r.avg_yield) if r.avg_yield else 0,
                "avg_farm_size": float(r.avg_farm_size) if r.avg_farm_size else 0,
            })

    return {"cantons": canton_data}
