"""
Aplicación principal FastAPI.

Punto de entrada de la aplicación que configura:
- Documentación Swagger/ReDoc
- Routers de API
- Templates Jinja2
- Manejo de errores
- Inicialización de base de datos
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.database import init_db
from app.api import auth

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Aplicación para el diagnóstico socioambiental en paisajes cacaoteros de Guayas y Los Ríos, Ecuador",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configurar templates Jinja2
templates = Jinja2Templates(directory="app/templates")

# Incluir routers
app.include_router(auth.router)


@app.on_event("startup")
def startup_event():
    """Inicializar base de datos al iniciar la aplicación."""
    init_db()


@app.get("/")
def root():
    """Página principal de la aplicación."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api": "/api",
    }


@app.get("/health")
def health_check():
    """Endpoint para verificación de salud de la aplicación."""
    return {"status": "healthy"}


# Importar y registrar routers adicionales
from app.api import kobo, dashboard, maps, data, reports

app.include_router(kobo.router)
app.include_router(dashboard.router)
app.include_router(maps.router)
app.include_router(data.router)
app.include_router(reports.router)

# Importar endpoints de vistas HTML
from app.api import views

app.include_router(views.router)
