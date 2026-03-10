"""
Servicio de KoboToolbox para importación y sincronización de datos.

Maneja la conexión con la API de KoboToolbox y la importación
de archivos CSV/Excel exportados desde KoboToolbox.
"""
import io
import json
from datetime import datetime
from typing import Any

import httpx
import pandas as pd
from geoalchemy2 import WKTElement
from sqlalchemy.orm import Session

from app.models.survey import Survey


class KoboService:
    """
    Servicio para integrarToolbox.

    datos de Kobo Maneja dos modos de ingesta:
    - API REST de KoboToolbox
    - Importación manual de archivos CSV/Excel
    """

    def __init__(self, db: Session):
        """
        Inicializa el servicio de Kobo.

        Args:
            db: Sesión de base de datos SQLAlchemy
        """
        self.db = db

    def sync_from_api(
        self,
        asset_uids: list[str],
        api_token: str,
        instance_url: str,
        mappings: dict[str, str]
    ) -> dict[str, int]:
        """
        Sincroniza datos desde la API de KoboToolbox.

        Args:
            asset_uids: Lista de asset UIDs a sincronizar
            api_token: Token de API de KoboToolbox
            instance_url: URL de la instancia de KoboToolbox
            mappings: Diccionario de mapeos de campos

        Returns:
            Diccionario con el conteo de registros importados y omitidos
        """
        headers = {"Authorization": f"Token {api_token}"}
        imported = 0
        skipped = 0

        for asset_uid in asset_uids:
            # Obtener datos del formulario
            url = f"{instance_url}/api/v2/assets/{asset_uid}/data/"
            params = {"format": "json"}

            with httpx.Client(timeout=60.0) as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                # Procesar cada registro
                for record in data.get("results", []):
                    if self._process_record(record, mappings):
                        imported += 1
                    else:
                        skipped += 1

        self.db.commit()
        return {"imported": imported, "skipped": skipped}

    def import_from_file(
        self,
        file: io.BytesIO,
        filename: str,
        mappings: dict[str, str]
    ) -> dict[str, int]:
        """
        Importa datos desde archivo CSV o Excel.

        Args:
            file: Archivo a importar
            filename: Nombre del archivo
            mappings: Diccionario de mapeos de campos

        Returns:
            Diccionario con el conteo de registros procesados, importados y omitidos
        """
        # Determinar tipo de archivo
        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            raise ValueError("Tipo de archivo no válido")

        processed = 0
        imported = 0
        skipped = 0

        # Procesar cada fila
        for _, row in df.iterrows():
            processed += 1
            record = row.to_dict()

            # Mapear nombres de columnas
            mapped_record = {}
            for col_name, value in record.items():
                # Buscar mapeo directo o usar nombre de columna
                internal_name = mappings.get(col_name, col_name)
                if internal_name in Survey.__table__.columns:
                    mapped_record[internal_name] = value

            if self._process_record(mapped_record, {}):
                imported += 1
            else:
                skipped += 1

        self.db.commit()
        return {"processed": processed, "imported": imported, "skipped": skipped}

    def _process_record(
        self,
        record: dict[str, Any],
        mappings: dict[str, str]
    ) -> bool:
        """
        Procesa un registro individual y lo guarda en la base de datos.

        Args:
            record: Datos del registro
            mappings: Mapeos de campos

        Returns:
            True si se importó, False si se omitió
        """
        # Obtener UUID de Kobo
        kobo_uuid = record.get("_uuid") or record.get("kobo_uuid")
        if not kobo_uuid:
            return False

        # Verificar si ya existe
        existing = self.db.query(Survey).filter(Survey.kobo_uuid == kobo_uuid).first()
        if existing:
            return False  # Omitir duplicados

        # Mapear campos
        mapped_data = {}
        for kobo_field, value in record.items():
            internal_field = mappings.get(kobo_field, kobo_field)
            if internal_field in Survey.__table__.columns:
                mapped_data[internal_field] = self._convert_value(internal_field, value)

        # Manejar coordenadas GPS
        lat = mapped_data.get("gps_latitude")
        lon = mapped_data.get("gps_longitude")

        if lat and lon:
            # Crear geometría PostGIS
            mapped_data["geom"] = WKTElement(f"POINT({lon} {lat})", srid=4326)

        # Convertir fechas
        if "_submission_time" in record:
            try:
                mapped_data["submission_date"] = datetime.fromisoformat(
                    record["_submission_time"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        # Crear registro
        survey = Survey(**mapped_data)
        self.db.add(survey)
        self.db.flush()

        return True

    def _convert_value(self, field_name: str, value: Any) -> Any:
        """
        Convierte valores según el tipo de campo.

        Args:
            field_name: Nombre del campo interno
            value: Valor a convertir

        Returns:
            Valor convertido
        """
        if value is None or pd.isna(value):
            return None

        # Campos numéricos
        if field_name in [
            "age", "farm_size_hectares", "total_income",
            "income_from_cacao", "income_from_other", "yield_quintals_per_ha",
            "forest_coverage_percent", "gps_latitude", "gps_longitude", "gps_accuracy"
        ]:
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        # Campos de fecha
        if field_name == "submission_date":
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    return None
            return value

        # Convertir a string para campos de texto
        return str(value) if not isinstance(value, str) else value
