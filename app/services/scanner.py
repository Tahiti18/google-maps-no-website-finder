"""Scanning service for finding businesses without websites."""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.models import Scan, ScanCity, Business, ScanResult
from app.models.scan import ScanStatus
from app.services.google_places import GooglePlacesService
from app.db import SessionLocal

logger = logging.getLogger(__name__)


class ScannerService:
    """Service for scanning businesses via Google Places API."""
    
    def __init__(self, google_service: Optional[GooglePlacesService] = None):
        """
        Initialize scanner service.
        
        Args:
            google_service: Google Places service instance
        """
        self.google_service = google_service or GooglePlacesService()
    
    def process_scan(self, scan_id: UUID) -> None:
        """
        Process a scan job.
        
        Args:
            scan_id: Scan ID to process
        """
        db = SessionLocal()
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if not scan:
                logger.error(f"Scan {scan_id} not found")
                return
            
            logger.info(f"Starting scan {scan_id}")
            scan.status = ScanStatus.RUNNING
            db.commit()
            
            try:
                self._execute_scan(db, scan)
                scan.status = ScanStatus.COMPLETED
                logger.info(f"Scan {scan_id} completed successfully")
            except Exception as e:
                logger.error(f"Scan {scan_id} failed: {e}", exc_info=True)
                scan.status = ScanStatus.FAILED
                scan.error_message = str(e)
            finally:
                db.commit()
        finally:
            db.close()
    
    def _execute_scan(self, db: Session, scan: Scan) -> None:
        """
        Execute the actual scanning logic.
        
        Args:
            db: Database session
            scan: Scan object
        """
        cities = db.query(ScanCity).filter(ScanCity.scan_id == scan.id).all()
        categories = scan.input_categories
        
        total_processed = 0
        total_without_website = 0
        total_with_website = 0
        
        # Process each city-category combination
        for city_obj in cities:
            for category in categories:
                logger.info(f"Scanning {category} in {city_obj.city_name}, {city_obj.state_abbr}")
                
                try:
                    # Search for places
                    places = self.google_service.search_places_by_city(
                        city=city_obj.city_name,
                        state=city_obj.state_abbr,
                        category=category
                    )
                    
                    # Process each place
                    for place in places:
                        place_id = place.get('place_id')
                        if not place_id:
                            continue
                        
                        try:
                            # Get detailed information
                            details = self.google_service.get_place_details(place_id)
                            
                            # Apply filters
                            if not self._passes_filters(details, scan):
                                continue
                            
                            total_processed += 1
                            
                            # Check website status
                            has_website = self.google_service.has_website(details)
                            if has_website:
                                total_with_website += 1
                            else:
                                total_without_website += 1
                            
                            # Create or update business
                            business = self._create_or_update_business(db, details, scan.id)
                            
                            # CRITICAL: Flush to get business.id assigned
                            db.flush()
                            
                            # Create scan result
                            self._create_scan_result(db, scan.id, business.id, has_website)
                            
                            # Commit periodically
                            if total_processed % 10 == 0:
                                db.commit()
                                logger.info(f"Processed {total_processed} businesses so far")
                        
                        except Exception as e:
                            logger.error(f"Error processing place {place_id}: {e}")
                            continue
                
                except Exception as e:
                    logger.error(f"Error scanning {category} in {city_obj.city_name}: {e}")
                    continue
        
        # Update scan statistics
        scan.total_businesses_processed = total_processed
        scan.total_without_website = total_without_website
        scan.total_with_website = total_with_website
        db.commit()
        
        logger.info(
            f"Scan completed: {total_processed} businesses processed, "
            f"{total_without_website} without website, "
            f"{total_with_website} with website"
        )
    
    def _passes_filters(self, place_details: Dict[str, Any], scan: Scan) -> bool:
        """
        Check if place passes scan filters.
        
        Args:
            place_details: Place details from API
            scan: Scan object with filters
            
        Returns:
            True if place passes all filters
        """
        # Must be operational
        if not self.google_service.is_operational(place_details):
            return False
        
        # Check rating filter
        if scan.min_rating is not None:
            rating = place_details.get('rating')
            if rating is None or rating < scan.min_rating:
                return False
        
        # Check reviews filter
        if scan.min_reviews is not None:
            reviews = place_details.get('user_ratings_total')
            if reviews is None or reviews < scan.min_reviews:
                return False
        
        return True
    
    def _create_or_update_business(
        self, 
        db: Session, 
        place_details: Dict[str, Any],
        scan_id: UUID
    ) -> Business:
        """
        Create or update a business record.
        
        Args:
            db: Database session
            place_details: Place details from API
            scan_id: Current scan ID
            
        Returns:
            Business object
        """
        place_id = place_details['place_id']
        
        # Check if business exists
        business = db.query(Business).filter(Business.place_id == place_id).first()
        
        if business:
            # Update existing business (optional fields may have changed)
            self._update_business_fields(business, place_details)
        else:
            # Create new business
            business = Business(place_id=place_id, first_seen_scan_id=scan_id)
            self._update_business_fields(business, place_details)
            db.add(business)
        
        return business
    
    def _update_business_fields(self, business: Business, place_details: Dict[str, Any]) -> None:
        """
        Update business fields from place details.
        
        Args:
            business: Business object
            place_details: Place details from API
        """
        # Extract location info
        location_info = self.google_service.extract_location_info(place_details)
        
        # Extract geometry
        geometry = place_details.get('geometry', {})
        location = geometry.get('location', {})
        
        # Update fields
        business.name = place_details.get('name', '')
        business.formatted_address = place_details.get('formatted_address')
        business.city = location_info['city']
        business.state = location_info['state']
        business.country = location_info['country'] or 'US'
        business.latitude = location.get('lat')
        business.longitude = location.get('lng')
        business.phone = place_details.get('formatted_phone_number')
        business.website = place_details.get('website')
        business.rating = place_details.get('rating')
        business.user_ratings_total = place_details.get('user_ratings_total')
        business.business_status = place_details.get('business_status')
        business.categories = place_details.get('types', [])
    
    def _create_scan_result(
        self, 
        db: Session, 
        scan_id: UUID, 
        business_id: int,
        has_website: bool
    ) -> None:
        """
        Create a scan result record.
        
        Args:
            db: Database session
            scan_id: Scan ID
            business_id: Business ID
            has_website: Whether business has website
        """
        # Check if result already exists for this scan-business pair
        existing = db.query(ScanResult).filter(
            ScanResult.scan_id == scan_id,
            ScanResult.business_id == business_id
        ).first()
        
        if not existing:
            result = ScanResult(
                scan_id=scan_id,
                business_id=business_id,
                has_website_at_scan_time=has_website
            )
            db.add(result)
