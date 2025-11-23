"""
RailFleet Manager API v1 endpoints.
"""
from . import auth, vehicles, maintenance, workshops, sync

__all__ = ["auth", "vehicles", "maintenance", "workshops", "sync"]
