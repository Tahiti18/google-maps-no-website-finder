"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import Base, get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """Create test client."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Override dependency
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    # Clean up
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_scan(client):
    """Test creating a scan."""
    scan_data = {
        "state": "CA",
        "cities": ["Los Angeles", "San Diego"],
        "categories": ["dentist", "plumber"],
        "min_rating": 4.0,
        "min_reviews": 10
    }
    
    response = client.post("/api/scans", json=scan_data)
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert data["status"] == "queued"
    assert data["input_state"] == "CA"
    assert data["cities_count"] == 2
    assert data["categories_count"] == 2


def test_create_scan_validation_error(client):
    """Test scan creation with invalid data."""
    # Missing required fields
    response = client.post("/api/scans", json={})
    assert response.status_code == 422
    
    # Invalid state
    response = client.post("/api/scans", json={
        "state": "CALIFORNIA",  # Should be 2 letters
        "cities": ["Los Angeles"],
        "categories": ["dentist"]
    })
    assert response.status_code == 422


def test_list_scans(client):
    """Test listing scans."""
    # Create a scan first
    scan_data = {
        "state": "CA",
        "cities": ["Los Angeles"],
        "categories": ["dentist"]
    }
    client.post("/api/scans", json=scan_data)
    
    # List scans
    response = client.get("/api/scans")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_scan_not_found(client):
    """Test getting non-existent scan."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/scans/{fake_uuid}")
    assert response.status_code == 404


def test_get_scan_results_not_found(client):
    """Test getting results for non-existent scan."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/scans/{fake_uuid}/results")
    assert response.status_code == 404
