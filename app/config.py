"""Application configuration."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database - HARDCODED for Railway internal networking
    # Railway Postgres is accessible via postgres.railway.internal:5432
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres.railway.internal:5432/railway"
    
    # Google API
    GOOGLE_MAPS_API_KEY: str = ""
    
    # Application
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # API Settings
    API_RATE_LIMIT_DELAY: float = 0.1
    MAX_RESULTS_PER_SEARCH: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
