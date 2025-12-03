"""Business schemas."""
from typing import Optional, List
from pydantic import BaseModel


class BusinessResponse(BaseModel):
    """Schema for business response."""
    id: int
    place_id: str
    name: str
    formatted_address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    phone: Optional[str]
    website: Optional[str]
    rating: Optional[float]
    user_ratings_total: Optional[int]
    business_status: Optional[str]
    categories: Optional[List[str]]
    maps_url: str
    
    class Config:
        from_attributes = True
