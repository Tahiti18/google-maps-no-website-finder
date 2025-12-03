"""Scan API endpoints."""
import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io
import json

from app.db import get_db
from app.models import Scan, ScanCity, Business, ScanResult
from app.models.scan import ScanStatus
from app.schemas import (
    ScanCreate,
    ScanResponse,
    ScanListResponse,
    ScanDetailResponse,
    BusinessResponse,
)
from app.services.worker import get_worker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scans", tags=["scans"])


@router.post("", response_model=ScanResponse, status_code=201)
def create_scan(scan_data: ScanCreate, db: Session = Depends(get_db)):
    """
    Create a new scan job.
    
    Args:
        scan_data: Scan creation data
        db: Database session
        
    Returns:
        Created scan
    """
    # Create scan
    scan = Scan(
        input_state=scan_data.state.upper(),
        input_categories=scan_data.categories,
        min_rating=scan_data.min_rating,
        min_reviews=scan_data.min_reviews,
        status=ScanStatus.QUEUED
    )
    db.add(scan)
    db.flush()  # Get scan ID
    
    # Add cities
    for city_name in scan_data.cities:
        city = ScanCity(
            scan_id=scan.id,
            city_name=city_name.strip(),
            state_abbr=scan_data.state.upper()
        )
        db.add(city)
    
    db.commit()
    db.refresh(scan)
    
    # Submit to worker
    worker = get_worker()
    worker.submit_scan(scan.id)
    
    logger.info(f"Created scan {scan.id}")
    
    return ScanResponse(
        id=scan.id,
        created_at=scan.created_at,
        status=scan.status,
        scan_type=scan.scan_type,
        input_state=scan.input_state,
        cities_count=len(scan_data.cities),
        categories_count=len(scan_data.categories)
    )


@router.get("", response_model=List[ScanListResponse])
def list_scans(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List recent scans.
    
    Args:
        limit: Maximum number of scans to return
        offset: Number of scans to skip
        db: Database session
        
    Returns:
        List of scans
    """
    scans = db.query(Scan).order_by(Scan.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for scan in scans:
        cities_count = db.query(ScanCity).filter(ScanCity.scan_id == scan.id).count()
        result.append(
            ScanListResponse(
                id=scan.id,
                created_at=scan.created_at,
                status=scan.status,
                input_state=scan.input_state,
                cities_count=cities_count,
                categories_count=len(scan.input_categories) if scan.input_categories else 0,
                total_businesses_processed=scan.total_businesses_processed,
                total_without_website=scan.total_without_website,
                total_with_website=scan.total_with_website
            )
        )
    
    return result


@router.get("/{scan_id}", response_model=ScanDetailResponse)
def get_scan(scan_id: UUID, db: Session = Depends(get_db)):
    """
    Get detailed information about a scan.
    
    Args:
        scan_id: Scan ID
        db: Database session
        
    Returns:
        Scan details
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    cities = db.query(ScanCity).filter(ScanCity.scan_id == scan_id).all()
    city_names = [f"{c.city_name}, {c.state_abbr}" for c in cities]
    
    return ScanDetailResponse(
        id=scan.id,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
        status=scan.status,
        scan_type=scan.scan_type,
        input_state=scan.input_state,
        input_categories=scan.input_categories or [],
        cities=city_names,
        min_rating=scan.min_rating,
        min_reviews=scan.min_reviews,
        total_businesses_processed=scan.total_businesses_processed,
        total_without_website=scan.total_without_website,
        total_with_website=scan.total_with_website,
        notes=scan.notes,
        error_message=scan.error_message
    )


@router.get("/{scan_id}/results")
def get_scan_results(
    scan_id: UUID,
    no_website_only: bool = Query(True, description="Filter to businesses without websites"),
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """
    Get scan results.
    
    Args:
        scan_id: Scan ID
        no_website_only: Only return businesses without websites
        format: Response format (json or csv)
        db: Database session
        
    Returns:
        Scan results in requested format
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Query results
    query = db.query(Business).join(
        ScanResult, ScanResult.business_id == Business.id
    ).filter(ScanResult.scan_id == scan_id)
    
    if no_website_only:
        query = query.filter(ScanResult.has_website_at_scan_time == False)
    
    businesses = query.all()
    
    if format == "json":
        results = [
            BusinessResponse(
                id=b.id,
                place_id=b.place_id,
                name=b.name,
                formatted_address=b.formatted_address,
                city=b.city,
                state=b.state,
                country=b.country,
                latitude=b.latitude,
                longitude=b.longitude,
                phone=b.phone,
                website=b.website,
                rating=b.rating,
                user_ratings_total=b.user_ratings_total,
                business_status=b.business_status,
                categories=b.categories,
                maps_url=b.maps_url
            )
            for b in businesses
        ]
        return results
    
    else:  # CSV format
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                'name', 'phone', 'formatted_address', 'city', 'state', 'country',
                'latitude', 'longitude', 'rating', 'user_ratings_total', 'maps_url'
            ]
        )
        writer.writeheader()
        
        for b in businesses:
            writer.writerow({
                'name': b.name or '',
                'phone': b.phone or '',
                'formatted_address': b.formatted_address or '',
                'city': b.city or '',
                'state': b.state or '',
                'country': b.country or '',
                'latitude': b.latitude or '',
                'longitude': b.longitude or '',
                'rating': b.rating or '',
                'user_ratings_total': b.user_ratings_total or '',
                'maps_url': b.maps_url
            })
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=scan_{scan_id}_results.csv"
            }
        )
