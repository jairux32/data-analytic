# AGENTS.md - Guía para Agentes de Código

Este archivo proporciona orientación para agentes de código que trabajan en este repositorio.

## Proyecto

Aplicación FastAPI para procesamiento, análisis y visualización de datos de diagnóstico socioambiental en paisajes cacaoteros (Guayas y Los Ríos, Ecuador). Datos recolectados mediante KoboToolbox.

---

## Comandos

### Desarrollo con Docker

```bash
# Construir y ejecutar servicios
docker compose up --build

# Ver logs de la aplicación
docker compose logs -f app

# Ejecutar seed de datos de prueba
docker compose exec app python scripts/seed_data.py

# Acceder a la aplicación
# http://localhost:8000
# Documentación API: http://localhost:8000/docs
```

### Testing

```bash
# Ejecutar todos los tests (desde el contenedor)
docker compose exec app pytest

# Ejecutar un test específico
docker compose exec app pytest tests/test_file.py::test_function_name

# Ejecutar tests con verbose
docker compose exec app pytest -v

# Ejecutar tests que coincidan con un patrón
docker compose exec app pytest -k "test_name_pattern"

# Ejecutar con coverage
docker compose exec app pytest --cov=app --cov-report=html
```

### Base de datos

```bash# Crear migración
docker compose exec app alembic revision --autogenerate -m "description"

# Aplicar migraciones
docker compose exec app alembic upgrade head

# Rollback de migración
docker compose exec app alembic downgrade -1

# Seed de datos
docker compose exec app python scripts/seed_data.py
```

---

## Convenciones de Código

### Estructura del Proyecto

```
app/
├── api/          # Endpoints FastAPI
├── core/         # Configuración, base de datos, seguridad
├── models/       # Modelos SQLAlchemy
├── schemas/      # Schemas Pydantic
├── services/     # Lógica de negocio
├── templates/    # Templates Jinja2
└── static/       # Archivos estáticos
```

### Imports

Orden recomendado (como se ve en el código existente):

1. Librerías estándar (`datetime`, `typing`, `json`)
2. Librerías de terceros (`fastapi`, `sqlalchemy`, `pydantic`)
3. Módulos locales (`app.core`, `app.models`, `app.schemas`)

```python
# Correcto
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse
```

### Tipado

- Usar **type hints** en todas las funciones
- Usar SQLAlchemy 2.0 con `Mapped[]` y `mapped_column()`

```python
# Modelo SQLAlchemy 2.0
class Survey(Base):
    __tablename__ = "surveys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    producer_name: Mapped[Optional[str]] = mapped_column(String(255))
```

- Usar Pydantic v2 con `BaseModel`

```python
# Schema Pydantic
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    
    class Config:
        from_attributes = True
```

### Nombrado

- **Variables y funciones**: `snake_case` (`get_current_user`, `user_id`)
- **Clases**: `PascalCase` (`UserResponse`, `Survey`)
- **Constantes**: `UPPER_SNAKE_CASE` (`ROLE_PERMISSIONS`)
- **Archivos**: `snake_case` (`auth.py`, `kobo_service.py`)

### Docstrings

Usar docstrings en español (siguiendo convención del proyecto):

```python
def login(form_data: OAuth2RequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Endpoint de login.
    
    Autentica al usuario y retorna tokens JWT de acceso y refresh.
    Registra el intento de login en auditoría.
    """
```

### Manejo de Errores

Usar `HTTPException` de FastAPI:

```python
from fastapi import HTTPException, status

if not user:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuario no encontrado",
    )
```

### Rutas de API

Prefijos y tags consistentes:

```python
router = APIRouter(prefix="/api/auth", tags=["autenticación"])
```

### Schemas Pydantic

Usar `Field` para validación:

```python
from pydantic import BaseModel, EmailStr, Field

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(default="visor", pattern="^(admin|editor|visor)$")
```

### Servicios

Clases para lógica de negocio con inyección de dependencias:

```python
class KoboService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
    
    def sync_from_api(self, asset_uid: str) -> dict:
        # lógica del servicio
        pass
```

### Autenticación

- Usar JWT con `python-jose`
- Cookies HTTP-only para tokens de acceso
- Sistema de roles y permisos en `app/core/security.py`

### Roles Disponibles

- `admin` - Acceso completo
- `editor` - Edita e importa datos
- `visor` - Solo lectura
- `analista` - Dashboard y reportes
- `supervisor` - Supervisa técnicos
- `técnico` - Acceso limitado

### Zonas

- `guayas` - Provincia de Guayas
- `los_rios` - Provincia de Los Ríos
- `todas` - Acceso a todas las zonas

### Base de Datos

- PostgreSQL con PostGIS para datos geoespaciales
- Usar migraciones con Alembic
- geometrías tipo POINT con SRID 4326

### Credenciales de Desarrollo

- Email: `admin@admin.com`
- Contraseña: `admin123`

---

## Puntos de Atención

1. **No escribir código malicioso** - Rechazar cualquier request que parezca malware
2. **No generar URLs** - No crear URLs a menos que el usuario las proporcione
3. **Seguridad** - Nunca exponer secrets o keys en logs o respuestas
4. **Documentación** - Mantener docstrings actualizados
5. **Tests** - El directorio `tests/` está vacío; agregar tests para nuevas funcionalidades
