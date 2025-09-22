"""Backward-compatible export for availability service."""
from services.availability import AvailabilityRequest, AvailabilityResponse, get_availability

__all__ = ["AvailabilityRequest", "AvailabilityResponse", "get_availability"]
