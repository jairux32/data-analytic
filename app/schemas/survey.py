"""
Schemas Pydantic para encuestas.

Define los esquemas para crear, actualizar y responder con datos de encuestas
de productores de cacao, organizados en las 4 dimensiones temáticas.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# === Schemas Base ===

class SurveyBase(BaseModel):
    """Schema base con campos comunes de encuesta."""
    # Socioeconómicos
    producer_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    education_level: Optional[str] = None
    province: Optional[str] = None
    canton: Optional[str] = None
    parish: Optional[str] = None
    farm_size_hectares: Optional[float] = None
    total_income: Optional[float] = None
    income_from_cacao: Optional[float] = None
    income_from_other: Optional[float] = None
    access_to_water: Optional[str] = None
    access_to_electricity: Optional[str] = None
    access_to_health: Optional[str] = None

    # Agronómicos
    cacao_varieties: Optional[str] = None
    yield_quintals_per_ha: Optional[float] = None
    use_of_fertilizers: Optional[str] = None
    use_of_organic: Optional[str] = None
    use_of_none: Optional[str] = None
    post_harvest_practices: Optional[str] = None
    member_of_organization: Optional[str] = None
    organization_name: Optional[str] = None
    access_to_technical_assistance: Optional[str] = None

    # Ambientales
    forest_coverage_percent: Optional[float] = None
    conservation_practices: Optional[str] = None
    protected_area_nearby: Optional[str] = None
    water_sources_on_farm: Optional[str] = None
    environmental_risks_perceived: Optional[str] = None

    # Gobernanza
    institutional_actors: Optional[str] = None
    access_to_credit: Optional[str] = None
    certifications: Optional[str] = None
    participation_in_decision_making: Optional[str] = None

    # GPS
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_accuracy: Optional[float] = None


# === Schemas de Request ===

class SurveyCreateRequest(SurveyBase):
    """Schema para crear una nueva encuesta."""
    kobo_uuid: str


class SurveyUpdateRequest(BaseModel):
    """Schema para actualizar una encuesta existente."""
    # Solo campos opcionales para actualización parcial
    producer_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    education_level: Optional[str] = None
    province: Optional[str] = None
    canton: Optional[str] = None
    parish: Optional[str] = None
    farm_size_hectares: Optional[float] = None
    total_income: Optional[float] = None
    income_from_cacao: Optional[float] = None
    income_from_other: Optional[float] = None
    access_to_water: Optional[str] = None
    access_to_electricity: Optional[str] = None
    access_to_health: Optional[str] = None
    cacao_varieties: Optional[str] = None
    yield_quintals_per_ha: Optional[float] = None
    use_of_fertilizers: Optional[str] = None
    use_of_organic: Optional[str] = None
    use_of_none: Optional[str] = None
    post_harvest_practices: Optional[str] = None
    member_of_organization: Optional[str] = None
    organization_name: Optional[str] = None
    access_to_technical_assistance: Optional[str] = None
    forest_coverage_percent: Optional[float] = None
    conservation_practices: Optional[str] = None
    protected_area_nearby: Optional[str] = None
    water_sources_on_farm: Optional[str] = None
    environmental_risks_perceived: Optional[str] = None
    institutional_actors: Optional[str] = None
    access_to_credit: Optional[str] = None
    certifications: Optional[str] = None
    participation_in_decision_making: Optional[str] = None


class SurveyFilterRequest(BaseModel):
    """Schema para filtros de búsqueda de encuestas."""
    province: Optional[str] = None
    canton: Optional[str] = None
    gender: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None


# === Schemas de Response ===

class SurveyResponse(SurveyBase):
    """Schema para respuesta de datos de encuesta."""
    id: int
    kobo_uuid: str
    asset_uid: Optional[str] = None
    submitter_id: Optional[str] = None
    submission_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SurveyListResponse(BaseModel):
    """Schema para lista paginada de encuestas."""
    total: int
    page: int
    per_page: int
    items: list[SurveyResponse]


# === Schemas para Dashboard ===

class DashboardKPIs(BaseModel):
    """KPIs generales del dashboard."""
    total_surveys: int
    total_provinces: int
    total_cantons: int
    avg_farm_size: Optional[float] = None
    avg_yield: Optional[float] = None


class SocioeconomicKPIs(BaseModel):
    """KPIs de dimensión socioeconómica."""
    total_producers: int
    by_province: dict
    by_gender: dict
    avg_age: Optional[float] = None
    education_distribution: dict
    avg_farm_size: float
    income_distribution: dict
    services_access: dict


class AgronomicKPIs(BaseModel):
    """KPIs de dimensión agronómica."""
    varieties_distribution: dict
    avg_yield: float
    fertilizer_usage: dict
    post_harvest_practices: dict
    organization_members: float
    technical_assistance_access: float


class EnvironmentalKPIs(BaseModel):
    """KPIs de dimensión ambiental."""
    avg_forest_coverage: float
    conservation_practices: dict
    protected_areas_nearby: float
    water_sources: dict
    environmental_risks: dict


class GovernanceKPIs(BaseModel):
    """KPIs de dimensión gobernanza."""
    institutional_actors: dict
    credit_access: float
    certifications: dict
    participation_in_decision_making: dict
