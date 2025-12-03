"""Application configuration."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database - can be full URL or individual components
    DATABASE_URL: Optional[str] = None
    PGHOST: Optional[str] = None
    PGPORT: Optional[str] = None
    PGUSER: Optional[str] = None
    PGPASSWORD: Optional[str] = None
    PGDATABASE: Optional[str] = None
    
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
    
    def get_database_url(self) -> str:
        """Get database URL, constructing from components if needed."""
        # If DATABASE_URL is set and valid, use it
        if self.DATABASE_URL and self.DATABASE_URL.strip() and not self.DATABASE_URL.startswith('${{'):
            return self.DATABASE_URL
        
        # Otherwise, construct from individual components
        if all([self.PGHOST, self.PGPORT, self.PGUSER, self.PGPASSWORD, self.PGDATABASE]):
            return f"postgresql://{self.PGUSER}:{self.PGPASSWORD}@{self.PGHOST}:{self.PGPORT}/{self.PGDATABASE}"
        
        # Fallback to localhost (for local development)
        return "postgresql://postgres:postgres@localhost:5432/gmaps_finder"


settings = Settings()
