"""
Configuración de la base de datos con SQLAlchemy y PostGIS.

Este módulo define la sesión de base de datos, el motor y las funciones
auxiliares para trabajar con PostgreSQL y PostGIS.
"""
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


class Base(DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy."""
    pass


# Motor de base de datos - usa NullPool para compatibilidad con containers
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=settings.debug,
    future=True,
)

# Habilitar PostGIS
@event.listens_for(engine, "connect")
def load_postgis(dbapi_connection, connection_record):
    """
    Habilita la extensión PostGIS al conectar a la base de datos.

    Esto permite usar tipos geométricos como POINT, POLYGON, etc.
    Si PostGIS no está disponible, continúa sin él.
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        cursor.close()
    except Exception as e:
        import logging
        logging.warning(f"No se pudo inicializar PostGIS en la conexión: {e}")
        try:
            dbapi_connection.rollback()
        except:
            pass


# SessionLocal factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependencia de FastAPI para obtener sesión de base de datos.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...

    Yields:
        Session: Sesión de base de datos
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Inicializa la base de datos creando todas las tablas.

    Esta función se debe llamar al iniciar la aplicación.
    Intenta hasta 5 veces para esperar a que PostgreSQL suba en entornos como Railway.
    """
    from app import models  # noqa: F401
    import time
    import logging
    from sqlalchemy.exc import OperationalError
    
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            # Validar conexión de forma atómica antes de crear metadatos
            with engine.connect() as connection:
                from sqlalchemy import text
                connection.execute(text("SELECT 1"))
                
            Base.metadata.create_all(bind=engine)
            print("Tablas de base de datos creadas exitosamente.")
            break
        except OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Error al conectar con la base de datos (Intento {attempt + 1}/{max_retries}). Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                print(f"No se pudo conectar a la base de datos después de {max_retries} intentos.")
                raise e
