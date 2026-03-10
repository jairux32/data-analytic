"""
Modelo de Mapeo de Campos para configuración flexible de KoboToolbox.

Permite relacionar los nombres de campos del formulario KoboToolbox
con los nombres de campos internos de la aplicación, facilitando
la adaptación a diferentes formularios sin cambiar código.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FieldMapping(Base):
    """
    Modelo para mapeo de campos entre KoboToolbox y la aplicación.

    Permite configurar qué campo del formulario Kobo corresponde
    a cada campo interno de la base de datos.
    """
    __tablename__ = "field_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kobo_field_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    internal_field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)  # string, number, date, select_one, select_multiple
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # socioeconomic, agronomic, environmental, governance, geospatial
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    default_value: Mapped[str] = mapped_column(String(255), nullable=True)
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
        return f"<FieldMapping(kobo={self.kobo_field_name} -> internal={self.internal_field_name})>"


# Mapeos por defecto para el formulario de diagnóstico cacaotero
DEFAULT_MAPPINGS = [
    # === Identificadores ===
    ("_uuid", "kobo_uuid", "string", "geospatial"),
    ("_asset_id", "asset_uid", "string", "geospatial"),
    ("_submitted_by", "submitter_id", "string", "geospatial"),
    ("_submission_time", "submission_date", "date", "geospatial"),

    # === Socioeconómicos ===
    ("producer_name", "producer_name", "string", "socioeconomic"),
    ("gender", "gender", "select_one", "socioeconomic"),
    ("age", "age", "number", "socioeconomic"),
    ("education_level", "education_level", "select_one", "socioeconomic"),
    ("province", "province", "select_one", "socioeconomic"),
    ("canton", "canton", "select_one", "socioeconomic"),
    ("parish", "parish", "select_one", "socioeconomic"),
    ("farm_size_hectares", "farm_size_hectares", "number", "socioeconomic"),
    ("total_income", "total_income", "number", "socioeconomic"),
    ("income_from_cacao", "income_from_cacao", "number", "socioeconomic"),
    ("income_from_other", "income_from_other", "number", "socioeconomic"),
    ("access_to_water", "access_to_water", "select_one", "socioeconomic"),
    ("access_to_electricity", "access_to_electricity", "select_one", "socioeconomic"),
    ("access_to_health", "access_to_health", "select_one", "socioeconomic"),

    # === Agronómicos ===
    ("cacao_varieties", "cacao_varieties", "select_multiple", "agronomic"),
    ("yield_quintals_per_ha", "yield_quintals_per_ha", "number", "agronomic"),
    ("use_of_fertilizers", "use_of_fertilizers", "select_one", "agronomic"),
    ("use_of_organic", "use_of_organic", "select_one", "agronomic"),
    ("use_of_none", "use_of_none", "select_one", "agronomic"),
    ("post_harvest_practices", "post_harvest_practices", "select_multiple", "agronomic"),
    ("member_of_organization", "member_of_organization", "select_one", "agronomic"),
    ("organization_name", "organization_name", "string", "agronomic"),
    ("access_to_technical_assistance", "access_to_technical_assistance", "select_one", "agronomic"),

    # === Ambientales ===
    ("forest_coverage_percent", "forest_coverage_percent", "number", "environmental"),
    ("conservation_practices", "conservation_practices", "select_multiple", "environmental"),
    ("protected_area_nearby", "protected_area_nearby", "select_one", "environmental"),
    ("water_sources_on_farm", "water_sources_on_farm", "select_multiple", "environmental"),
    ("environmental_risks_perceived", "environmental_risks_perceived", "select_multiple", "environmental"),

    # === Gobernanza ===
    ("institutional_actors", "institutional_actors", "select_multiple", "governance"),
    ("access_to_credit", "access_to_credit", "select_one", "governance"),
    ("certifications", "certifications", "select_multiple", "governance"),
    ("participation_in_decision_making", "participation_in_decision_making", "select_multiple", "governance"),

    # === GPS ===
    ("gps_latitude", "gps_latitude", "number", "geospatial"),
    ("gps_longitude", "gps_longitude", "number", "geospatial"),
    ("gps_accuracy", "gps_accuracy", "number", "geospatial"),
]
