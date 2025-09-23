"""Backward-compatible export for availability service."""
from services.availability.models import AvailabilityRequest, AvailabilityResponse
from services.availability.service import get_availability

__all__ = ["AvailabilityRequest", "AvailabilityResponse", "get_availability"]
