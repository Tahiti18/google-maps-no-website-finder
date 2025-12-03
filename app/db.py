"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings

# Base class for models (defined first, no DB connection needed)
Base = declarative_base()

# Lazy initialization of engine
_engine = None
_SessionLocal = None

def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        database_url = settings.get_database_url()
        _engine = create_engine(
            database_url,
            pool_pre_ping=True,
            echo=(settings.APP_ENV == "development")
        )
    return _engine

def get_session_local():
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

# For backward compatibility
engine = property(lambda self: get_engine())
SessionLocal = property(lambda self: get_session_local())


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Yields:
        Database session
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
