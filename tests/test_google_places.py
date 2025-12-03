"""Tests for Google Places service."""
import pytest
from unittest.mock import Mock, patch
from app.services.google_places import GooglePlacesService


@pytest.fixture
def google_service():
    """Create Google Places service instance."""
    return GooglePlacesService(api_key="test_key")


def test_is_operational(google_service):
    """Test business status check."""
    # Operational business
    assert google_service.is_operational({'business_status': 'OPERATIONAL'}) is True
    
    # Non-operational business
    assert google_service.is_operational({'business_status': 'CLOSED_TEMPORARILY'}) is False
    assert google_service.is_operational({'business_status': 'CLOSED_PERMANENTLY'}) is False
    assert google_service.is_operational({}) is False


def test_has_website(google_service):
    """Test website detection."""
    # Has website
    assert google_service.has_website({'website': 'https://example.com'}) is True
    
    # No website
    assert google_service.has_website({'website': ''}) is False
    assert google_service.has_website({'website': '   '}) is False
    assert google_service.has_website({}) is False


def test_extract_location_info(google_service):
    """Test location extraction from address components."""
    address_components = [
        {'types': ['locality'], 'long_name': 'Los Angeles', 'short_name': 'LA'},
        {'types': ['administrative_area_level_1'], 'long_name': 'California', 'short_name': 'CA'},
        {'types': ['country'], 'long_name': 'United States', 'short_name': 'US'},
    ]
    
    result = google_service.extract_location_info({'address_components': address_components})
    
    assert result['city'] == 'Los Angeles'
    assert result['state'] == 'CA'
    assert result['country'] == 'US'


def test_extract_location_info_incomplete(google_service):
    """Test location extraction with incomplete data."""
    address_components = [
        {'types': ['locality'], 'long_name': 'Los Angeles'},
    ]
    
    result = google_service.extract_location_info({'address_components': address_components})
    
    assert result['city'] == 'Los Angeles'
    assert result['state'] is None
    assert result['country'] is None


@patch('app.services.google_places.requests.get')
def test_search_places_by_city(mock_get, google_service):
    """Test searching places by city."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        'status': 'OK',
        'results': [
            {'place_id': 'test1', 'name': 'Business 1'},
            {'place_id': 'test2', 'name': 'Business 2'},
        ]
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    results = google_service.search_places_by_city('Los Angeles', 'CA', 'dentist')
    
    assert len(results) == 2
    assert results[0]['place_id'] == 'test1'
    assert results[1]['place_id'] == 'test2'


@patch('app.services.google_places.requests.get')
def test_get_place_details(mock_get, google_service):
    """Test getting place details."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        'status': 'OK',
        'result': {
            'place_id': 'test123',
            'name': 'Test Business',
            'website': 'https://test.com',
            'business_status': 'OPERATIONAL'
        }
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    details = google_service.get_place_details('test123')
    
    assert details['place_id'] == 'test123'
    assert details['name'] == 'Test Business'
    assert details['website'] == 'https://test.com'


@patch('app.services.google_places.requests.get')
def test_api_error_handling(mock_get, google_service):
    """Test API error handling."""
    # Mock error response
    mock_response = Mock()
    mock_response.json.return_value = {
        'status': 'REQUEST_DENIED',
        'error_message': 'Invalid API key'
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    with pytest.raises(Exception) as exc_info:
        google_service.search_places_by_city('Los Angeles', 'CA', 'dentist')
    
    assert 'REQUEST_DENIED' in str(exc_info.value)
