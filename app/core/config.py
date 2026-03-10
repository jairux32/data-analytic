"""
Configuración de la aplicación utilizando Pydantic Settings.

Este módulo define las variables de entorno necesarias para la aplicación
y proporciona validación automática de tipos.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración de la aplicación basada en variables de entorno.

    Utiliza Pydantic Settings para validación automática y transformación
    de tipos. Los valores se leen del archivo .env o variables de entorno.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "Diagnóstico Socioambiental Cacaotero"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"

    # Database
    database_url: str = "postgresql://kobo_cacao:kobo_cacao_pass@localhost:5432/kobo_cacao_db"

    # Security
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # KoboToolbox
    kobo_instance_url: str = "https://kf.kobotoolbox.org"
    kobo_api_token: Optional[str] = None
    kobo_asset_uids: Optional[str] = None
    kobo_sync_interval_hours: int = 0

    # SMTP
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

    # Export
    export_temp_dir: str = "/tmp/exports"
    export_cleanup_days: int = 7

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def kobo_asset_list(self) -> list[str]:
        """Retorna lista de asset UIDs configurados."""
        if not self.kobo_asset_uids:
            return []
        return [uid.strip() for uid in self.kobo_asset_uids.split(",") if uid.strip()]


@lru_cache()
def get_settings() -> Settings:
    """
    Obtiene la configuración de la aplicación (cached).

    Returns:
        Settings: Instancia de configuración con los valores del entorno
    """
    return Settings()


# Instancia global de configuración
settings = get_settings()
