"""Scan result model linking scans and businesses."""
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from app.db import Base


class ScanResult(Base):
    """Link table between scans and businesses."""
    
    __tablename__ = "scan_results"
    
    id = Column(Integer, primary_key=True)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    
    # Track website status at time of scan
    has_website_at_scan_time = Column(Boolean, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    scan = relationship("Scan", back_populates="results")
    business = relationship("Business", back_populates="scan_results")
    
    def __repr__(self):
        return f"<ScanResult scan={self.scan_id} business={self.business_id}>"


# Create indexes for efficient queries
Index('idx_scan_results_scan', ScanResult.scan_id)
Index('idx_scan_results_business', ScanResult.business_id)
Index('idx_scan_results_no_website', ScanResult.scan_id, ScanResult.has_website_at_scan_time)
