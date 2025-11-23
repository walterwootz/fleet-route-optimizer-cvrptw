"""
RailFleet Manager API v1 endpoints.
"""
from . import auth, vehicles, maintenance, workshops, sync, scheduler, transfer, hr, docs, policy

__all__ = ["auth", "vehicles", "maintenance", "workshops", "sync", "scheduler", "transfer", "hr", "docs", "policy"]
