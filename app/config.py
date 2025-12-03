"""Application configuration."""
import os
import sys
from typing import Optional
from pydantic_settings import BaseSettings

# Print ALL environment variables for debugging
print("=" * 80, file=sys.stderr)
print("ENVIRONMENT VARIABLES:", file=sys.stderr)
for key, value in os.environ.items():
    if 'PG' in key or 'DATABASE' in key or 'POSTGRES' in key:
        # Mask password
        if 'PASSWORD' in key:
            print(f"{key}=***MASKED***", file=sys.stderr)
        else:
            print(f"{key}={value}", file=sys.stderr)
print("=" * 80, file=sys.stderr)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
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
        case_sensitive = False  # Changed to False to be more flexible
    
    @property
    def DATABASE_URL(self) -> str:
        """Get database URL from environment."""
        # Check all possible environment variable names Railway might use
        for key in ['DATABASE_URL', 'DATABASE_PUBLIC_URL', 'POSTGRES_URL', 'POSTGRESQL_URL']:
            url = os.environ.get(key)
            if url:
                print(f"Found database URL in {key}", file=sys.stderr)
                return url
        
        # Try to construct from parts
        pghost = os.environ.get('PGHOST')
        pgport = os.environ.get('PGPORT', '5432')
        pguser = os.environ.get('PGUSER', 'postgres')
        pgpassword = os.environ.get('PGPASSWORD', '')
        pgdatabase = os.environ.get('PGDATABASE', 'railway')
        
        if pghost:
            url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}"
            print(f"Constructed URL from PG variables: postgresql://{pguser}:***@{pghost}:{pgport}/{pgdatabase}", file=sys.stderr)
            return url
        
        print("WARNING: No database configuration found, using localhost", file=sys.stderr)
        return "postgresql://postgres:postgres@localhost:5432/gmaps_finder"


settings = Settings()
