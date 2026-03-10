"""
Paquete de schemas Pydantic.

Este paquete exporta todos los schemas para facilitar la importación
desde otros módulos de la aplicación.
"""
from app.schemas.auth import (
    LoginRequest,
    TokenRequest,
    TokenResponse,
    UserResponse,
    UserCreateRequest,
    UserUpdateRequest,
    UserListResponse,
    MessageResponse,
    ErrorResponse,
)
from app.schemas.survey import (
    SurveyBase,
    SurveyCreateRequest,
    SurveyUpdateRequest,
    SurveyResponse,
    SurveyListResponse,
    SurveyFilterRequest,
    DashboardKPIs,
    SocioeconomicKPIs,
    AgronomicKPIs,
    EnvironmentalKPIs,
    GovernanceKPIs,
)
from app.schemas.kobo import (
    FieldMappingBase,
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

__all__ = [
    # Auth
    "LoginRequest",
    "TokenRequest",
    "TokenResponse",
    "UserResponse",
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserListResponse",
    "MessageResponse",
    "ErrorResponse",
    # Survey
    "SurveyBase",
    "SurveyCreateRequest",
    "SurveyUpdateRequest",
    "SurveyResponse",
    "SurveyListResponse",
    "SurveyFilterRequest",
    "DashboardKPIs",
    "SocioeconomicKPIs",
    "AgronomicKPIs",
    "EnvironmentalKPIs",
    "GovernanceKPIs",
    # Kobo
    "FieldMappingBase",
    "FieldMappingCreate",
    "FieldMappingUpdate",
    "FieldMappingResponse",
    "SyncRequest",
    "SyncStatusResponse",
    "SyncResponse",
    "UploadResponse",
    "KoboConfigResponse",
    "KoboConfigUpdate",
]
