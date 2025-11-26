"""
Hybrid Database Configuration
Unterstützt sowohl SQLite (lokal) als auch Supabase/PostgreSQL (remote)
Wechselt automatisch zwischen beiden basierend auf Verfügbarkeit
"""

import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator, Optional
import requests

logger = logging.getLogger(__name__)

# Supabase Configuration
SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "https://supabasekong-s0wkccwgk84w0o8ww8s8wccs.luli-server.de:8000"
)
SUPABASE_SERVICE_KEY = os.getenv(
    "SUPABASE_SERVICE_KEY",
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzdXBhYmFzZSIsImlhdCI6MTc2MzEzNzUwMCwiZXhwIjo0OTE4ODExMTAwLCJyb2xlIjoic2VydmljZV9yb2xlIn0._oIZyDQ_2EEc4UnrUg7Ch9xGVeNvm8gb_xclh3N2JqA"
)

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "supabasekong-s0wkccwgk84w0o8ww8s8wccs.luli-server.de")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "VDt5mjy92lGDWQuE6OpfaHxX9XvFEjEw")

# SQLite Configuration (Fallback)
SQLITE_URL = "sqlite:///./railfleet.db"

# Database URLs
POSTGRES_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


def test_supabase_connection(timeout: int = 5) -> bool:
    """Testet ob Supabase erreichbar ist"""
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"
        }
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/",
            headers=headers,
            timeout=timeout
        )
        return response.status_code in [200, 404]  # 404 ist ok, bedeutet API läuft
    except Exception as e:
        logger.debug(f"Supabase not reachable: {e}")
        return False


def test_postgres_connection(timeout: int = 5) -> bool:
    """Testet ob PostgreSQL erreichbar ist"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=int(POSTGRES_PORT),
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            connect_timeout=timeout
        )
        conn.close()
        return True
    except Exception as e:
        logger.debug(f"PostgreSQL not reachable: {e}")
        return False


def get_database_url() -> tuple[str, str]:
    """
    Ermittelt die beste verfügbare Datenbank-URL
    
    Returns:
        Tuple[str, str]: (database_url, database_type)
    """
    # Prüfe ob Supabase/PostgreSQL erreichbar ist
    if test_postgres_connection(timeout=3):
        logger.info("✅ Using PostgreSQL (Supabase)")
        return POSTGRES_URL, "postgresql"
    
    # Fallback zu SQLite
    logger.info("⚠️  PostgreSQL not reachable, using SQLite")
    return SQLITE_URL, "sqlite"


# Ermittle die beste Datenbank
DATABASE_URL, DATABASE_TYPE = get_database_url()

# Engine-Konfiguration basierend auf Datenbank-Typ
if DATABASE_TYPE == "sqlite":
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    logger.info(f"🗄️  Database: SQLite (Local)")
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False
    )
    logger.info(f"🗄️  Database: PostgreSQL (Supabase)")

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base für Models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency für FastAPI um DB-Session zu erhalten
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_database_info() -> dict:
    """Gibt Informationen über die aktuelle Datenbank zurück"""
    return {
        "type": DATABASE_TYPE,
        "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
        "engine": str(engine.url),
        "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else None
    }


def init_db():
    """
    Initialize database - create all tables.
    This should be called on application startup.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables initialized")


# Logging
logger.info("=" * 70)
logger.info("🚀 DATABASE HYBRID CONFIGURATION")
logger.info("=" * 70)
logger.info(f"   Type: {DATABASE_TYPE.upper()}")
logger.info(f"   URL:  {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
logger.info("=" * 70)

