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
    """Inicializar base de datos al iniciar la aplicación, esperando a que esté disponible."""
    import time
    import logging
    from sqlalchemy.exc import OperationalError
    
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            init_db()
            break
        except Exception as e:
            # psycopg2.OperationalError a menudo viene embebido como causa original
            if "Connection refused" in str(e) or isinstance(e, OperationalError) or "OperationalError" in str(e):
                if attempt < max_retries - 1:
                    logging.warning(f"Esperando a la base de datos (Intento {attempt + 1}/{max_retries}). Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    logging.error(f"Falla crítica: No se pudo conectar a la base luego de {max_retries} intentos.")
                    raise e
            else:
                raise e


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
