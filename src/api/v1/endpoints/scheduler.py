"""
Scheduler endpoints - Proxy to solver service.
"""
from fastapi import APIRouter, HTTPException, status
import httpx
import os
from typing import Dict, Any

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])

SOLVER_URL = os.getenv("SOLVER_URL", "http://localhost:7070")


@router.post("/solve")
async def solve(problem: Dict[str, Any]):
    """
    Solve workshop scheduling problem (proxy to solver service).

    Forwards request to solver microservice and returns solution.
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{SOLVER_URL}/solve", json=problem)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Solver timeout - problem too complex or service unavailable"
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Solver service error: {str(e)}"
        )


@router.get("/health")
async def solver_health():
    """Check solver service health."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{SOLVER_URL}/health")
            return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Solver service unavailable: {str(e)}"
        )
