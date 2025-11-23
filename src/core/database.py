"""
Database configuration and session management.
Uses SQLAlchemy 2.0 with async support.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os

# Database URL from environment or default to PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://railfleet:railfleet123@localhost:5432/railfleet_db"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,
    max_overflow=10,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency for FastAPI to get database session.

    Yields:
        Database session

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.
    This should be called on application startup.
    """
    Base.metadata.create_all(bind=engine)
