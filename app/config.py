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
        import os
        
        # Try environment variable directly (Railway sets this)
        db_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PUBLIC_URL')
        if db_url and db_url.strip() and not db_url.startswith('${{') and not db_url.startswith('"'):
            # Clean up any quotes
            db_url = db_url.strip('"').strip("'")
            if db_url and not db_url.startswith('${{'):
                return db_url
        
        # Try from self.DATABASE_URL
        if self.DATABASE_URL and self.DATABASE_URL.strip():
            url = self.DATABASE_URL.strip('"').strip("'")
            if url and not url.startswith('${{'):
                return url
        
        # Otherwise, construct from individual components
        pghost = self.PGHOST or os.environ.get('PGHOST')
        pgport = self.PGPORT or os.environ.get('PGPORT')
        pguser = self.PGUSER or os.environ.get('PGUSER')
        pgpassword = self.PGPASSWORD or os.environ.get('PGPASSWORD')
        pgdatabase = self.PGDATABASE or os.environ.get('PGDATABASE')
        
        if all([pghost, pgport, pguser, pgpassword, pgdatabase]):
            return f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}"
        
        # Fallback to localhost (for local development only)
        return "postgresql://postgres:postgres@localhost:5432/gmaps_finder"


settings = Settings()
