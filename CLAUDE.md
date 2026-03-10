# CLAUDE.md

Este archivo proporciona orientación a Claude Code (claude.ai/code) cuando trabaja con el código de este repositorio.

## Proyecto

Aplicación FastAPI para el procesamiento, análisis y visualización de datos de diagnóstico socioambiental en paisajes cacaoteros de las provincias de Guayas y Los Ríos, Ecuador. Los datos se recolectan mediante KoboToolbox.

## Comandos

```bash
# Desarrollo con Docker
docker compose up --build

# Ver logs
docker compose logs -f app

# Ejecutar seed de datos de prueba
docker compose exec app python scripts/seed_data.py

# Acceder a la aplicación
# http://localhost:8000
# Documentación API: http://localhost:8000/docs
```

## Credenciales por Defecto

- Email: admin@admin.com
- Contraseña: admin123

## Configuración

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Generar SECRET_KEY segura
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Arquitectura

```
app/
├── api/          # Endpoints FastAPI (auth, dashboard, maps, data, reports, kobo, views)
├── core/         # Configuración (config.py), base de datos (database.py), seguridad (security.py)
├── models/       # Modelos SQLAlchemy (Survey, User, FieldMapping, SyncLog, AuditLog)
├── schemas/      # Schemas Pydantic para validación
├── services/     # Lógica de negocio (KoboService)
├── templates/    # Templates HTML/Jinja2 (dashboard, maps, tables, admin)
└── static/       # Archivos estáticos
```

### Stack Principal

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Base de datos**: PostgreSQL con PostGIS (geometrías POINT)
- **Frontend**: Tailwind CSS, HTMX, Plotly, Leaflet
- **Cache**: Redis
- **Contenedores**: Docker Compose

### Endpoints Principales

- `POST /api/auth/login` - Autenticación JWT
- `GET /api/dashboard/*` - KPIs por dimensión (socioeconómica, agronómica, ambiental, gobernanza)
- `GET /api/maps/points` - Puntos GPS para Leaflet
- `POST /api/kobo/sync` - Sincronización con KoboToolbox API
- `POST /api/kobo/upload` - Importación manual CSV/Excel

### Roles y Permisos

Sistema granular con 6 roles (definidos en `app/core/security.py`):
- `admin` - Acceso completo
- `editor` - Edita e importa datos
- `visor` - Solo lectura
- `analista` - Dashboard y reportes
- `supervisor` - Supervisa técnicos
- `técnico` - Acceso limitado

Cada usuario tiene una **zona** asignada (guayas, los_rios, todas) para filtrar datos geográficos.

### Endpoints de Gestión de Usuarios

- `POST /api/auth/register` - Crear usuario
- `GET /api/auth/users` - Listar con filtros
- `GET /api/auth/users/{id}` - Ver usuario
- `PUT /api/auth/users/{id}` - Actualizar usuario
- `DELETE /api/auth/users/{id}` - Desactivar usuario
- `POST /api/auth/users/{id}/activate` - Activar usuario
- `POST /api/auth/users/{id}/reset-password` - Resetear contraseña
- `GET /api/auth/me/permissions` - Ver mis permisos
- `GET /api/auth/roles` - Listar roles y permisos
- `GET /api/auth/audit` - Ver logs de auditoría

### Modelo de Datos Principal

`Survey` contiene campos organizados en 4 dimensiones:
- Socioeconómica: producer_name, age, farm_size_hectares, income_*, access_to_*
- Agronómica: cacao_varieties, yield_quintals_per_ha, use_of_fertilizers, post_harvest_practices
- Ambiental: forest_coverage_percent, conservation_practices, water_sources_on_farm
- Gobernanza: institutional_actors, access_to_credit, certifications

Los datos geoespaciales se almacenan en PostGIS (campo `geom` tipo POINT, SRID 4326).

### Integración KoboToolbox

`KoboService` maneja la importación mediante:
1. API REST de KoboToolbox (`sync_from_api`)
2. Archivos CSV/Excel (`import_from_file`)

Los mapeos de campos se configuran en `FieldMapping` y permiten transformar nombres de columnas de Kobo a nombres internos.
