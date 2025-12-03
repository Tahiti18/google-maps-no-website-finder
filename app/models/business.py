"""Business model."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime

from app.db import Base


class Business(Base):
    """Business model representing a place from Google Maps."""
    
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True)
    place_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    formatted_address = Column(Text, nullable=True)
    
    # Location
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    country = Column(String(2), nullable=True, default="US")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Contact
    phone = Column(String(50), nullable=True)
    website = Column(Text, nullable=True)
    
    # Ratings
    rating = Column(Float, nullable=True)
    user_ratings_total = Column(Integer, nullable=True)
    
    # Status
    business_status = Column(String(50), nullable=True)
    
    # Categories (Google types)
    categories = Column(JSONB, nullable=True)
    
    # Tracking
    first_seen_scan_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    scan_results = relationship("ScanResult", back_populates="business")
    
    def __repr__(self):
        return f"<Business {self.name} - {self.place_id}>"
    
    @property
    def maps_url(self) -> str:
        """Generate Google Maps URL for this business."""
        return f"https://www.google.com/maps/place/?q=place_id:{self.place_id}"


# Create index for common queries
Index('idx_business_city_state', Business.city, Business.state)
Index('idx_business_website_null', Business.website)
