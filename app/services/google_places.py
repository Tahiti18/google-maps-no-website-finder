"""Google Places API integration."""
import logging
import time
from typing import Dict, List, Optional, Any
import requests

from app.config import settings

logger = logging.getLogger(__name__)


class GooglePlacesService:
    """Service for interacting with Google Places API."""
    
    BASE_URL = "https://maps.googleapis.com/maps/api"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Places service.
        
        Args:
            api_key: Google Maps API key (defaults to settings)
        """
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        if not self.api_key:
            raise ValueError("Google Maps API key is required")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to Google Places API.
        
        Args:
            endpoint: API endpoint path
            params: Request parameters
            
        Returns:
            JSON response
            
        Raises:
            Exception: If API request fails
        """
        params['key'] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check API status
            status = data.get('status')
            if status not in ['OK', 'ZERO_RESULTS']:
                error_msg = data.get('error_message', 'Unknown error')
                logger.error(f"Google Places API error: {status} - {error_msg}")
                raise Exception(f"Google Places API error: {status} - {error_msg}")
            
            return data
        except requests.RequestException as e:
            logger.error(f"Request to Google Places API failed: {e}")
            raise
    
    def search_places_by_city(
        self, 
        city: str, 
        state: str, 
        category: str,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for places in a city by category using Text Search.
        
        Args:
            city: City name
            state: State abbreviation
            category: Business category (e.g., "dentist")
            max_results: Maximum number of results to return
            
        Returns:
            List of place results
        """
        query = f"{category} in {city}, {state}"
        logger.info(f"Searching: {query}")
        
        all_results = []
        next_page_token = None
        max_results = max_results or settings.MAX_RESULTS_PER_SEARCH
        
        while True:
            params = {
                'query': query,
                'type': 'establishment'
            }
            
            if next_page_token:
                params['pagetoken'] = next_page_token
                # Google requires a short delay before using next_page_token
                time.sleep(2)
            
            data = self._make_request('place/textsearch/json', params)
            
            results = data.get('results', [])
            all_results.extend(results)
            
            logger.info(f"Found {len(results)} results for '{query}' (total: {len(all_results)})")
            
            # Check if we should continue pagination
            next_page_token = data.get('next_page_token')
            if not next_page_token or len(all_results) >= max_results:
                break
            
            # Rate limiting
            time.sleep(settings.API_RATE_LIMIT_DELAY)
        
        return all_results[:max_results]
    
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a place.
        
        Args:
            place_id: Google Place ID
            
        Returns:
            Place details dictionary
        """
        params = {
            'place_id': place_id,
            'fields': (
                'place_id,name,formatted_address,geometry,business_status,'
                'formatted_phone_number,website,rating,user_ratings_total,'
                'types,address_components'
            )
        }
        
        data = self._make_request('place/details/json', params)
        
        # Rate limiting
        time.sleep(settings.API_RATE_LIMIT_DELAY)
        
        return data.get('result', {})
    
    def extract_location_info(self, place_details: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Extract city, state, and country from address components.
        
        Args:
            place_details: Place details from API
            
        Returns:
            Dictionary with city, state, country
        """
        address_components = place_details.get('address_components', [])
        
        city = None
        state = None
        country = None
        
        for component in address_components:
            types = component.get('types', [])
            
            if 'locality' in types:
                city = component.get('long_name')
            elif 'administrative_area_level_1' in types:
                state = component.get('short_name')
            elif 'country' in types:
                country = component.get('short_name')
        
        return {
            'city': city,
            'state': state,
            'country': country
        }
    
    def is_operational(self, place_details: Dict[str, Any]) -> bool:
        """
        Check if business is operational.
        
        Args:
            place_details: Place details from API
            
        Returns:
            True if operational
        """
        status = place_details.get('business_status', '').upper()
        return status == 'OPERATIONAL'
    
    def has_website(self, place_details: Dict[str, Any]) -> bool:
        """
        Check if business has a website listed.
        
        Args:
            place_details: Place details from API
            
        Returns:
            True if website exists
        """
        website = place_details.get('website', '').strip()
        return bool(website)
