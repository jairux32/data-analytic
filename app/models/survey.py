"""
Modelo de Encuesta para almacenar datos de productores de cacao.

Este es el modelo principal que almacena todos los datos de las encuestas
recolectadas mediante KoboToolbox, organizados en las 4 dimensiones:
- Socioeconómica
- Agronómica
- Ambiental
- Gobernanza
"""
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Survey(Base):
    """
    Modelo de encuesta de diagnóstico socioambiental cacaotero.

    Almacena los datos de cada productor encuestado en las 4 dimensiones
    definidas por el proyecto. Utiliza PostGIS para almacenar coordenadas GPS.
    """
    __tablename__ = "surveys"

    # === Identificadores ===
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kobo_uuid: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    asset_uid: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    submitter_id: Mapped[Optional[str]] = mapped_column(String(255))
    submission_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # === Dimensión Socioeconómica ===
    producer_name: Mapped[Optional[str]] = mapped_column(String(255))
    gender: Mapped[Optional[str]] = mapped_column(String(50))  # masculino, femenino
    age: Mapped[Optional[int]] = mapped_column(Integer)
    education_level: Mapped[Optional[str]] = mapped_column(String(100))
    province: Mapped[Optional[str]] = mapped_column(String(100))  # Guayas, Los Ríos
    canton: Mapped[Optional[str]] = mapped_column(String(100))
    parish: Mapped[Optional[str]] = mapped_column(String(100))
    farm_size_hectares: Mapped[Optional[float]] = mapped_column(Float)
    total_income: Mapped[Optional[float]] = mapped_column(Float)
    income_from_cacao: Mapped[Optional[float]] = mapped_column(Float)
    income_from_other: Mapped[Optional[float]] = mapped_column(Float)
    access_to_water: Mapped[Optional[str]] = mapped_column(String(50))  # sí, no
    access_to_electricity: Mapped[Optional[str]] = mapped_column(String(50))
    access_to_health: Mapped[Optional[str]] = mapped_column(String(50))

    # === Dimensión Agronómica ===
    cacao_varieties: Mapped[Optional[str]] = mapped_column(Text)  # múltiplaselection: CCN-51, Nacional, etc.
    yield_quintals_per_ha: Mapped[Optional[float]] = mapped_column(Float)
    use_of_fertilizers: Mapped[Optional[str]] = mapped_column(String(50))  # sí, no
    use_of_organic: Mapped[Optional[str]] = mapped_column(String(50))
    use_of_none: Mapped[Optional[str]] = mapped_column(String(50))
    post_harvest_practices: Mapped[Optional[str]] = mapped_column(Text)  # fermentación, secado, etc.
    member_of_organization: Mapped[Optional[str]] = mapped_column(String(50))
    organization_name: Mapped[Optional[str]] = mapped_column(String(255))
    access_to_technical_assistance: Mapped[Optional[str]] = mapped_column(String(50))

    # === Dimensión Ambiental ===
    forest_coverage_percent: Mapped[Optional[float]] = mapped_column(Float)
    conservation_practices: Mapped[Optional[str]] = mapped_column(Text)  # múltiples prácticas
    protected_area_nearby: Mapped[Optional[str]] = mapped_column(String(50))
    water_sources_on_farm: Mapped[Optional[str]] = mapped_column(Text)  # río, quebrada, pozo
    environmental_risks_perceived: Mapped[Optional[str]] = mapped_column(Text)  # sequía, inundación, deforestación

    # === Dimensión Gobernanza ===
    institutional_actors: Mapped[Optional[str]] = mapped_column(Text)  # MAG, PNG, etc.
    access_to_credit: Mapped[Optional[str]] = mapped_column(String(50))
    certifications: Mapped[Optional[str]] = mapped_column(Text)  # UTZ, Rainforest, Orgánico
    participation_in_decision_making: Mapped[Optional[str]] = mapped_column(Text)

    # === Datos Geoespaciales (PostGIS) ===
    gps_latitude: Mapped[Optional[float]] = mapped_column(Float)
    gps_longitude: Mapped[Optional[float]] = mapped_column(Float)
    gps_accuracy: Mapped[Optional[float]] = mapped_column(Float)
    geom: Mapped[Optional[Geometry]] = mapped_column(Geometry("POINT", srid=4326))

    # === Metadatos ===
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Survey(id={self.id}, producer={self.producer_name}, province={self.province})>"
