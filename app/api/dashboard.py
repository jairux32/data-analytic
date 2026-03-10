"""
API de Dashboard para análisis de datos.

Endpoints para obtener KPIs y visualizaciones de las 4 dimensiones:
- Socioeconómica
- Agronómica
- Ambiental
- Gobernanza
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.survey import Survey
from app.schemas.survey import (
    SocioeconomicKPIs,
    AgronomicKPIs,
    EnvironmentalKPIs,
    GovernanceKPIs,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/socioeconomic", response_model=SocioeconomicKPIs)
def get_socioeconomic_data(
    province: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene KPIs de la dimensión socioeconómica."""
    query = db.query(Survey)

    if province:
        query = query.filter(Survey.province == province)
    if gender:
        query = query.filter(Survey.gender == gender)

    total = query.count()

    # Distribución por provincia
    province_dist = query.with_entities(
        Survey.province, func.count(Survey.id)
    ).group_by(Survey.province).all()
    by_province = {p: c for p, c in province_dist if p}

    # Distribución por género
    gender_dist = query.with_entities(
        Survey.gender, func.count(Survey.id)
    ).group_by(Survey.gender).all()
    by_gender = {g: c for g, c in gender_dist if g}

    # Edad promedio
    avg_age = query.with_entities(func.avg(Survey.age)).scalar()

    # Nivel de educación
    education_dist = query.with_entities(
        Survey.education_level, func.count(Survey.id)
    ).group_by(Survey.education_level).all()
    education_distribution = {e: c for e, c in education_dist if e}

    # Tamaño promedio de finca
    avg_farm_size = query.with_entities(
        func.avg(Survey.farm_size_hectares)
    ).scalar() or 0

    # Ingresos
    income_dist = query.with_entities(
        func.avg(Survey.total_income),
        func.avg(Survey.income_from_cacao),
        func.avg(Survey.income_from_other)
    ).first()
    avg_total = income_dist[0] if income_dist else None
    avg_cacao = income_dist[1] if income_dist else None
    avg_other = income_dist[2] if income_dist else None
    income_distribution = {
        "avg_total": avg_total if avg_total else 0,
        "avg_cacao": avg_cacao if avg_cacao else 0,
        "avg_other": avg_other if avg_other else 0,
    }

    # Acceso a servicios
    water = query.filter(Survey.access_to_water == "sí").count()
    electricity = query.filter(Survey.access_to_electricity == "sí").count()
    health = query.filter(Survey.access_to_health == "sí").count()
    services_access = {
        "water": water,
        "electricity": electricity,
        "health": health,
        "total": total
    }

    return SocioeconomicKPIs(
        total_producers=total,
        by_province=by_province,
        by_gender=by_gender,
        avg_age=avg_age,
        education_distribution=education_distribution,
        avg_farm_size=avg_farm_size or 0,
        income_distribution=income_distribution,
        services_access=services_access,
    )


@router.get("/agronomic", response_model=AgronomicKPIs)
def get_agronomic_data(
    province: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene KPIs de la dimensión agronómica."""
    query = db.query(Survey)

    if province:
        query = query.filter(Survey.province == province)
    if gender:
        query = query.filter(Survey.gender == gender)

    # Distribución de variedades
    varieties_data = query.with_entities(
        Survey.cacao_varieties
    ).all()
    varieties_count = {}
    for v in varieties_data:
        if v[0]:
            for variety in v[0].split():
                varieties_count[variety] = varieties_count.get(variety, 0) + 1

    # Rendimiento promedio
    avg_yield = query.with_entities(
        func.avg(Survey.yield_quintals_per_ha)
    ).scalar() or 0

    # Uso de fertilizantes
    fertilizers = query.filter(Survey.use_of_fertilizers == "sí").count()
    organic = query.filter(Survey.use_of_organic == "sí").count()
    none = query.filter(Survey.use_of_none == "sí").count()
    fertilizer_usage = {
        "fertilizers": fertilizers,
        "organic": organic,
        "none": none,
        "total": query.count()
    }

    # Prácticas postcosecha
    post_harvest = query.with_entities(
        Survey.post_harvest_practices
    ).all()
    post_harvest_count = {}
    for p in post_harvest:
        if p[0]:
            for practice in p[0].split():
                post_harvest_count[practice] = post_harvest_count.get(practice, 0) + 1

    # Miembros de organización
    org_members = query.filter(Survey.member_of_organization == "sí").count()
    total = query.count()
    organization_members = (org_members / total * 100) if total > 0 else 0

    # Asistencia técnica
    tech_assist = query.filter(Survey.access_to_technical_assistance == "sí").count()
    technical_assistance_access = (tech_assist / total * 100) if total > 0 else 0

    return AgronomicKPIs(
        varieties_distribution=varieties_count,
        avg_yield=avg_yield,
        fertilizer_usage=fertilizer_usage,
        post_harvest_practices=post_harvest_count,
        organization_members=organization_members,
        technical_assistance_access=technical_assistance_access,
    )


@router.get("/environmental", response_model=EnvironmentalKPIs)
def get_environmental_data(
    province: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene KPIs de la dimensión ambiental."""
    query = db.query(Survey)

    if province:
        query = query.filter(Survey.province == province)
    if gender:
        query = query.filter(Survey.gender == gender)

    # Cobertura forestal promedio
    avg_forest = query.with_entities(
        func.avg(Survey.forest_coverage_percent)
    ).scalar() or 0

    # Prácticas de conservación
    conservation = query.with_entities(
        Survey.conservation_practices
    ).all()
    conservation_count = {}
    for c in conservation:
        if c[0]:
            for practice in c[0].split():
                conservation_count[practice] = conservation_count.get(practice, 0) + 1

    # Áreas protegidas cercanas
    protected = query.filter(Survey.protected_area_nearby == "sí").count()
    total = query.count()
    protected_areas_nearby = (protected / total * 100) if total > 0 else 0

    # Fuentes de agua
    water_sources = query.with_entities(
        Survey.water_sources_on_farm
    ).all()
    water_count = {}
    for w in water_sources:
        if w[0]:
            for source in w[0].split():
                water_count[source] = water_count.get(source, 0) + 1

    # Riesgos ambientales percibidos
    risks = query.with_entities(
        Survey.environmental_risks_perceived
    ).all()
    risk_count = {}
    for r in risks:
        if r[0]:
            for risk in r[0].split():
                risk_count[risk] = risk_count.get(risk, 0) + 1

    return EnvironmentalKPIs(
        avg_forest_coverage=avg_forest,
        conservation_practices=conservation_count,
        protected_areas_nearby=protected_areas_nearby,
        water_sources=water_count,
        environmental_risks=risk_count,
    )


@router.get("/governance", response_model=GovernanceKPIs)
def get_governance_data(
    province: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene KPIs de la dimensión de gobernanza."""
    query = db.query(Survey)

    if province:
        query = query.filter(Survey.province == province)
    if gender:
        query = query.filter(Survey.gender == gender)

    # Actores institucionales
    actors = query.with_entities(
        Survey.institutional_actors
    ).all()
    actors_count = {}
    for a in actors:
        if a[0]:
            for actor in a[0].split():
                actors_count[actor] = actors_count.get(actor, 0) + 1

    # Acceso a crédito
    credit = query.filter(Survey.access_to_credit == "sí").count()
    total = query.count()
    credit_access = (credit / total * 100) if total > 0 else 0

    # Certificaciones
    certs = query.with_entities(
        Survey.certifications
    ).all()
    certs_count = {}
    for c in certs:
        if c[0]:
            for cert in c[0].split():
                certs_count[cert] = certs_count.get(cert, 0) + 1

    # Participación en toma de decisiones
    participation = query.with_entities(
        Survey.participation_in_decision_making
    ).all()
    participation_count = {}
    for p in participation:
        if p[0]:
            for item in p[0].split():
                participation_count[item] = participation_count.get(item, 0) + 1

    return GovernanceKPIs(
        institutional_actors=actors_count,
        credit_access=credit_access,
        certifications=certs_count,
        participation_in_decision_making=participation_count,
    )
