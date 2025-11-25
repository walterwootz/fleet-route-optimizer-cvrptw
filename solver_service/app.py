"""
RailFleet Solver Service - FastAPI Application

Microservice for workshop scheduling using OR-Tools CP-SAT.
Runs independently on port 7070.
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from solver_core import RailFleetSolver

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RailFleet Solver Service",
    description="Workshop Scheduling Solver using OR-Tools CP-SAT",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to backend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class SolveRequest(BaseModel):
    """Solve request with problem specification."""
    problem: Dict[str, Any]
    tracks: List[Dict[str, Any]]
    teams: List[Dict[str, Any]]
    parts: List[Dict[str, Any]]
    work_orders: List[Dict[str, Any]]
    objectives: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
    solver_config: Optional[Dict[str, Any]] = None


class SolveResponse(BaseModel):
    """Solve response with assignments and metrics."""
    status: str
    solver_status: Optional[str] = None
    objective_value: Optional[float] = None
    solve_time_sec: Optional[float] = None
    assignments: List[Dict[str, Any]]
    unscheduled: List[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/", tags=["Root"])
def root():
    """Root endpoint."""
    return {
        "service": "RailFleet Solver",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "POST /solve - Solve scheduling problem",
            "GET /health - Health check",
        ],
    }


@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "solver",
        "version": "1.0.0",
    }


@app.post("/solve", response_model=SolveResponse, tags=["Solver"])
def solve(request: SolveRequest):
    """
    Solve workshop scheduling problem.

    Takes work orders, tracks, teams, and parts as input.
    Returns optimal/feasible schedule with assignments.

    **Constraints:**
    - No-Overlap (tracks, teams)
    - Skills matching
    - Parts availability
    - Time windows & deadlines
    - Asset incompatibilities

    **Objectives:**
    - Minimize unscheduled work orders
    - Minimize lateness
    - Minimize overtime
    """
    try:
        logger.info("Received solve request")
        logger.info(f"Work Orders: {len(request.work_orders)}")
        logger.info(f"Tracks: {len(request.tracks)}")
        logger.info(f"Teams: {len(request.teams)}")

        # Initialize solver
        time_unit = request.problem.get("time_unit_min", 15)
        solver = RailFleetSolver(time_unit_min=time_unit)

        # Solve
        solution = solver.solve(request.model_dump())

        logger.info(f"Solve completed: {solution['status']}")
        logger.info(f"Scheduled: {len(solution.get('assignments', []))}")
        logger.info(f"Unscheduled: {len(solution.get('unscheduled', []))}")

        return SolveResponse(**solution)

    except Exception as e:
        logger.error(f"Solver error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Solver error: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """Startup event."""
    logger.info("RailFleet Solver Service starting up...")
    logger.info("OR-Tools CP-SAT ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event."""
    logger.info("RailFleet Solver Service shutting down...")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=7070,
        log_level="info",
        reload=False  # Disable reload in production
    )
