"""Application configuration."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database - HARDCODED for Railway public proxy
    # Using the public proxy domain from Railway Postgres settings
    DATABASE_URL: str = "postgresql://postgres:postgres@ballast.proxy.rlwy.net:22302/railway"
    
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
