"""Scan model."""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime
import enum
import uuid

from app.db import Base


class ScanStatus(str, enum.Enum):
    """Scan status enum."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanType(str, enum.Enum):
    """Scan type enum."""
    CITY_BASED = "city_based"
    GRID_BASED = "grid_based"  # For future use


class Scan(Base):
    """Scan model representing a search job."""
    
    __tablename__ = "scans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.QUEUED, nullable=False)
    scan_type = Column(SQLEnum(ScanType), default=ScanType.CITY_BASED, nullable=False)
    
    input_state = Column(String(2), nullable=False)  # e.g., "CA"
    input_categories = Column(JSONB, nullable=False)  # e.g., ["dentist", "plumber"]
    
    # Optional filters
    min_rating = Column(Float, nullable=True)
    min_reviews = Column(Integer, nullable=True)
    
    # Summary counts
    total_businesses_processed = Column(Integer, default=0)
    total_without_website = Column(Integer, default=0)
    total_with_website = Column(Integer, default=0)
    
    # Error tracking
    notes = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    cities = relationship("ScanCity", back_populates="scan", cascade="all, delete-orphan")
    results = relationship("ScanResult", back_populates="scan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Scan {self.id} - {self.status.value}>"


class ScanCity(Base):
    """Cities associated with a scan."""
    
    __tablename__ = "scan_cities"
    
    id = Column(Integer, primary_key=True)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    city_name = Column(String(100), nullable=False)
    state_abbr = Column(String(2), nullable=False)
    
    # Relationship
    scan = relationship("Scan", back_populates="cities")
    
    def __repr__(self):
        return f"<ScanCity {self.city_name}, {self.state_abbr}>"
