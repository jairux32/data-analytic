# Diagnóstico Socioambiental en Paisajes Cacaoteros

Aplicación web completa para el procesamiento, análisis y visualización de datos recolectados mediante KoboToolbox, correspondientes a un diagnóstico socioambiental integral en paisajes cacaoteros de las provincias de Guayas y Los Ríos, Ecuador.

## Características

- **Autenticación JWT** con 3 roles: admin, editor, visor
- **Dashboard analítico** con 4 dimensiones temáticas:
  - Socioeconómica
  - Agronómica
  - Ambiental
  - Gobernanza
- **Mapas geoespaciales** con Leaflet.js
- **Tablas de datos** con paginación server-side
- **Exportaciones** a PDF y Excel
- **Integración con KoboToolbox**:
  - Sincronización via API REST
  - Importación manual de CSV/Excel

## Requisitos

- Docker y Docker Compose
- PostgreSQL con extensión PostGIS

## Instalación

### 1. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 2. Iniciar servicios con Docker Compose

```bash
docker-compose up --build
```

### 3. Acceder a la aplicación

- URL: http://localhost:8000
- Documentación API: http://localhost:8000/docs

### 4. Credenciales por defecto

- Email: admin@admin.com
- Contraseña: admin123

## Uso del Script de Seed

Para generar datos de prueba:

```bash
docker-compose exec app python scripts/seed_data.py
```

Esto creará:
- 50 registros ficticios de productores de cacao
- Datos realistas con coordenadas GPS en Guayas y Los Ríos

## Estructura del Proyecto

```
kobo_cacao_app/
├── app/
│   ├── api/           # Endpoints FastAPI
│   ├── core/          # Configuración
│   ├── models/        # Modelos SQLAlchemy
│   ├── schemas/       # Schemas Pydantic
│   ├── services/      # Lógica de negocio
│   ├── templates/     # Templates HTML/Jinja2
│   └── static/        # Archivos estáticos
├── scripts/           # Scripts de utilidad
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## API Endpoints

### Autenticación
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Usuario actual
- `POST /api/auth/register` - Registrar usuario (admin)

### Dashboard
- `GET /api/dashboard/socioeconomic` - KPIs socioeconómicos
- `GET /api/dashboard/agronomic` - KPIs agronómicos
- `GET /api/dashboard/environmental` - KPIs ambientales
- `GET /api/dashboard/governance` - KPIs gobernanza

### Mapas
- `GET /api/maps/points` - Puntos GPS de encuestas
- `GET /api/maps/heatmap` - Datos para heatmap

### Datos
- `GET /api/data/surveys` - Lista paginada de encuestas
- `GET /api/data/filters` - Opciones de filtros

### Reportes
- `GET /api/reports/pdf` - Exportar a PDF
- `GET /api/reports/excel` - Exportar a Excel

### KoboToolbox
- `POST /api/kobo/sync` - Sincronizar con Kobo API
- `POST /api/kobo/upload` - Importar archivo CSV/Excel
- `GET /api/kobo/mappings` - Ver mapeos de campos

## Tecnologías

- **Backend**: Python 3.11, FastAPI
- **Base de datos**: PostgreSQL, PostGIS
- **ORM**: SQLAlchemy
- **Frontend**: Tailwind CSS, HTMX, Plotly, Leaflet
- **Exportación**: ReportLab, OpenPyXL

## Licencia

MIT
