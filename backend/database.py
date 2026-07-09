"""
Configuración de la conexión a la base de datos.

Lee DATABASE_URL del entorno. Por defecto usa SQLite local; en producción
(Railway/Render) se inyecta una URL de PostgreSQL.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///crossfit.db")
# Railway entrega "postgres://" o "postgresql://"; forzamos el driver psycopg v3
# (psycopg2 no está instalado, solo psycopg[binary]).
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

_es_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if _es_sqlite else {}

# Pool explícito solo para Postgres (SQLite no usa pool de conexiones). Dimensionado
# para ~30 usuarios concurrentes: 10 conexiones fijas + hasta 20 de desborde.
_pool_kwargs = {} if _es_sqlite else {"pool_size": 10, "max_overflow": 20}

engine = create_engine(
    DATABASE_URL,
    echo=_es_sqlite,
    connect_args=connect_args,
    pool_pre_ping=True,
    **_pool_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Generador de sesiones para inyección de dependencias."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
