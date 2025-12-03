"""Scan schemas."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.scan import ScanStatus, ScanType


class ScanCreate(BaseModel):
    """Schema for creating a new scan."""
    state: str = Field(..., min_length=2, max_length=2, description="State abbreviation (e.g., CA)")
    cities: List[str] = Field(..., min_items=1, description="List of city names")
    categories: List[str] = Field(..., min_items=1, description="List of business categories")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating filter")
    min_reviews: Optional[int] = Field(None, ge=0, description="Minimum review count filter")


class ScanResponse(BaseModel):
    """Basic scan response."""
    id: UUID
    created_at: datetime
    status: ScanStatus
    scan_type: ScanType
    input_state: str
    cities_count: int
    categories_count: int
    
    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    """Response for listing scans."""
    id: UUID
    created_at: datetime
    status: ScanStatus
    input_state: str
    cities_count: int
    categories_count: int
    total_businesses_processed: int
    total_without_website: int
    total_with_website: int
    
    class Config:
        from_attributes = True


class ScanDetailResponse(BaseModel):
    """Detailed scan response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: ScanStatus
    scan_type: ScanType
    input_state: str
    input_categories: List[str]
    cities: List[str]
    min_rating: Optional[float]
    min_reviews: Optional[int]
    total_businesses_processed: int
    total_without_website: int
    total_with_website: int
    notes: Optional[str]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True
