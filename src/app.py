"""Main application entry point for RailFleet Manager."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Original solver routes
from .api import router as solver_router

# RailFleet Manager routes
from .api.v1.endpoints import auth, vehicles, maintenance, workshops, sync, scheduler, transfer, hr, docs, policy, parts, stock, procurement, finance, reports, events, projections, sync_crdt, time_travel, ml, analytics, fleet_one, database_agent

# Database-backed routes (Phase 2)
from .api.routes_db import vehicles_db, maintenance_db, workshop_db

# Database (Hybrid: SQLite + Supabase)
from .core.database_hybrid import init_db, get_database_info

# Logging
from .config import setup_logging, get_settings, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="RailFleet Manager API",
    description="""
    **RailFleet Manager** - Complete Railway Fleet Management System

    **Features:**
    - 🤖 **FLEET-ONE Agent**: LLM-based intelligent fleet management assistant (German)
    - 🚂 **Fleet Management**: Track locomotives, maintenance, and operations
    - 🔧 **Maintenance Management**: Schedule and track maintenance tasks and work orders
    - 🏭 **Workshop Management**: Manage workshops, capacity, and certifications
    - 🚚 **Transfer Service**: Plan and track locomotive movements between locations
    - 👥 **HR Service**: Staff management and personnel assignment planning
    - 📄 **Document Management**: ECM-Light with expiration tracking and audit trail
    - 📦 **Inventory Management**: Parts, stock locations, and stock moves tracking
    - 🛒 **Procurement**: Supplier management and purchase order workflow (DRAFT → CLOSED)
    - 💰 **Finance**: Invoice management, PO matching, and budget tracking with variance analysis
    - 📈 **Reporting & KPIs**: Availability, on-time ratio, parts usage, and cost reports
    - 📊 **Advanced Analytics**: Real-time dashboards with KPIs, time series, and insights
    - 🔄 **Offline-First Sync**: Conflict detection and resolution for mobile/offline use
    - 🔐 **Authentication & Authorization**: Role-based access control (RBAC)
    - 🚛 **Route Optimization**: CVRPTW solver with OR-Tools and Gurobi
    - 📅 **Workshop Scheduler**: OR-Tools CP-SAT based scheduling with constraints

    **Powered by FLEET-ONE: Central AI agent with multi-mode routing and policy-based conflict resolution**
    """,
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include RailFleet Manager API routes
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(vehicles.router, prefix="/api/v1", tags=["Vehicles"])
app.include_router(maintenance.router, prefix="/api/v1", tags=["Maintenance"])
app.include_router(workshops.router, prefix="/api/v1", tags=["Workshops"])
app.include_router(sync.router, prefix="/api/v1", tags=["Synchronization"])
app.include_router(scheduler.router, prefix="/api/v1", tags=["Scheduler"])
app.include_router(transfer.router, prefix="/api/v1", tags=["Transfer"])
app.include_router(hr.router, prefix="/api/v1", tags=["HR"])
app.include_router(docs.router, prefix="/api/v1", tags=["Documents"])
app.include_router(policy.router, prefix="/api/v1", tags=["Policy"])
app.include_router(parts.router, prefix="/api/v1", tags=["Inventory"])
app.include_router(stock.router, prefix="/api/v1", tags=["Inventory"])
app.include_router(procurement.router, prefix="/api/v1", tags=["Procurement"])
app.include_router(finance.router, prefix="/api/v1", tags=["Finance"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])
app.include_router(events.router, prefix="/api/v1", tags=["Events"])
app.include_router(projections.router, prefix="/api/v1", tags=["Projections"])
app.include_router(sync_crdt.router, prefix="/api/v1", tags=["CRDT Synchronization"])
app.include_router(time_travel.router, prefix="/api/v1", tags=["Time-Travel & Audit"])
app.include_router(ml.router, prefix="/api/v1", tags=["Machine Learning"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(fleet_one.router, prefix="/api/v1", tags=["FLEET-ONE Agent"])
app.include_router(database_agent.router, prefix="/api/v1/database-agent", tags=["Database Agent"])

# Include original CVRPTW solver routes
app.include_router(solver_router, prefix="/api/v1/solver", tags=["Route Optimization"])

# Include Database-backed routes (Phase 2 - Real Data)
app.include_router(vehicles_db.router, tags=["Vehicles (DB)"])
app.include_router(maintenance_db.router, tags=["Maintenance (DB)"])
app.include_router(workshop_db.router, tags=["Workshop (DB)"])


@app.get("/", tags=["Root"])
def root():
    """Root endpoint with API information."""
    return {
        "name": "RailFleet Manager API",
        "version": "2.1.0",
        "description": "Complete Railway Fleet Management System with Route Optimization",
        "docs": "/docs",
        "features": [
            "Fleet Management",
            "Maintenance Tracking",
            "Workshop Management",
            "Transfer Service",
            "HR & Staff Management",
            "Document Management (ECM-Light)",
            "Inventory Management",
            "Procurement & PO Management",
            "Finance & Budget Tracking",
            "Reporting & KPIs",
            "Advanced Analytics Dashboard",
            "Offline-First Sync",
            "Route Optimization (CVRPTW)",
            "Workshop Scheduler (CP-SAT)",
        ],
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("RailFleet Manager starting up...")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("RailFleet Manager shutting down...")


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )
