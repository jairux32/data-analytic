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
    """
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
