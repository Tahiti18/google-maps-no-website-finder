"""Application configuration."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/gmaps_finder"
    
    # Google API
    GOOGLE_MAPS_API_KEY: str = ""
    
    # Application
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # API Settings
    API_RATE_LIMIT_DELAY: float = 0.1  # Delay between API calls in seconds
    
    # Scanning Settings
    MAX_RESULTS_PER_SEARCH: int = 60  # Google Places returns up to 60 results (3 pages of 20)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
