"""Database models."""
from app.models.scan import Scan, ScanCity
from app.models.business import Business
from app.models.scan_result import ScanResult

__all__ = ["Scan", "ScanCity", "Business", "ScanResult"]
