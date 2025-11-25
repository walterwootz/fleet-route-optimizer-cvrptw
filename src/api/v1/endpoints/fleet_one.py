"""
FLEET-ONE Agent API Endpoints

REST API for FLEET-ONE central fleet management agent.

Endpoints:
- POST /fleet-one/query - Main query endpoint
- POST /fleet-one/session - Create session
- GET /fleet-one/session/{session_id}/history - Get session history
- DELETE /fleet-one/session/{session_id} - Clear session
- GET /fleet-one/modes - List available modes
- GET /fleet-one/metrics - Get agent metrics
- GET /fleet-one/health - Health check
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime, date

from src.database import get_db
from src.services.fleet_one import (
    get_agent,
    get_handlers,
    get_orchestrator,
    AgentMode,
    init_policy_engine,
    init_orchestrator,
    init_handlers
)
from src.services.event_store import EventStore
import json
import os


router = APIRouter(prefix="/fleet-one", tags=["FLEET-ONE Agent"])


# Request/Response Models

class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    session_id: Optional[str] = None
    user_id: str
    user_role: str = "dispatcher"
    force_mode: Optional[str] = None


class QueryResponse(BaseModel):
    """Query response model"""
    session_id: str
    text: str
    mode: str
    tool_calls: List[Dict[str, Any]]
    suggestions: List[str]
    warnings: List[str]
    data: Optional[Dict[str, Any]] = None


class SessionRequest(BaseModel):
    """Session creation request"""
    user_id: str
    user_role: str = "dispatcher"


class SessionResponse(BaseModel):
    """Session response"""
    session_id: str
    user_id: str
    role: str


class UseCaseRequest(BaseModel):
    """Generic use case request"""
    use_case: str
    params: Dict[str, Any]
    user_role: str = "dispatcher"


# Initialize FLEET-ONE components on startup

def _ensure_initialized():
    """Ensure FLEET-ONE components are initialized"""
    # Load policy config
    policy_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "config", "fleet_one_policy.json")

    try:
        with open(policy_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        # Use minimal config if file not found
        config = {
            "version": "1.0.0",
            "tools": [],
            "policy": {"conflict_matrix": []}
        }

    # Initialize components
    if get_orchestrator() is None:
        init_orchestrator(config)

    if get_handlers() is None:
        orchestrator = get_orchestrator()
        if orchestrator:
            init_handlers(orchestrator)

    # Initialize policy engine
    policy_rules = config.get("policy", {}).get("conflict_matrix", [])
    init_policy_engine(policy_rules)

    # Get or create agent
    get_agent(config)


# API Endpoints

@router.post("/query", response_model=QueryResponse)
def query_agent(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Main FLEET-ONE query endpoint.

    Processes user queries in German and returns responses with tool calls.

    Example:
        POST /fleet-one/query
        {
            "query": "Zeig mir alle Loks, die in den nächsten 30 Tagen zur HU müssen",
            "user_id": "user123",
            "user_role": "dispatcher"
        }
    """
    _ensure_initialized()

    agent = get_agent()

    # Create or get session
    if not request.session_id:
        session_id = agent.create_session(
            user_id=request.user_id,
            role=request.user_role
        )
    else:
        session_id = request.session_id

    # Parse force_mode if provided
    force_mode = None
    if request.force_mode:
        try:
            force_mode = AgentMode(request.force_mode.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mode: {request.force_mode}"
            )

    # Process query
    try:
        response = agent.process_query(
            session_id=session_id,
            query=request.query,
            force_mode=force_mode
        )

        # Log as event
        event_store = EventStore(db)
        event_store.append_event(
            aggregate_type="FleetOneAgent",
            aggregate_id=session_id,
            event_type="QueryProcessed",
            data={
                "query": request.query,
                "mode": response.mode.value,
                "user_id": request.user_id,
                "user_role": request.user_role
            },
            metadata={"service": "fleet-one"}
        )
        db.commit()

        return QueryResponse(
            session_id=session_id,
            text=response.text,
            mode=response.mode.value,
            tool_calls=response.tool_calls,
            suggestions=response.suggestions,
            warnings=response.warnings,
            data=response.data
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/session", response_model=SessionResponse)
def create_session(request: SessionRequest):
    """
    Create new conversation session.

    Returns session ID that should be used for subsequent queries.
    """
    _ensure_initialized()

    agent = get_agent()
    session_id = agent.create_session(
        user_id=request.user_id,
        role=request.user_role
    )

    return SessionResponse(
        session_id=session_id,
        user_id=request.user_id,
        role=request.user_role
    )


@router.get("/session/{session_id}/history")
def get_session_history(session_id: str):
    """Get conversation history for session"""
    _ensure_initialized()

    agent = get_agent()
    history = agent.get_session_history(session_id)

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    return {"session_id": session_id, "history": history}


@router.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear session data"""
    _ensure_initialized()

    agent = get_agent()
    success = agent.clear_session(session_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    return {"status": "cleared", "session_id": session_id}


@router.get("/modes")
def list_modes():
    """List available agent modes"""
    return {
        "modes": [
            {
                "id": mode.value,
                "name": mode.value,
                "description": f"{mode.value} operations"
            }
            for mode in AgentMode
        ]
    }


@router.post("/use-case/{use_case_name}")
def execute_use_case(
    use_case_name: str,
    request: UseCaseRequest,
    db: Session = Depends(get_db)
):
    """
    Execute specific use case directly.

    Use cases:
    - hu_planning: Plan HU maintenance
    - parts_procurement: Check parts and order
    - transfer_staff: Plan transfer staff
    - invoice_entry: Enter invoice
    - documents: Document management
    - vehicle_status: Update vehicle status
    - availability_report: Get availability report
    - maintenance_task: Create maintenance task
    """
    _ensure_initialized()

    handlers = get_handlers()
    if not handlers:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Use case handlers not initialized"
        )

    # Route to appropriate handler
    try:
        if use_case_name == "hu_planning":
            result = handlers.handle_hu_planning(
                workshop_id=request.params.get("workshop_id"),
                days_ahead=request.params.get("days_ahead", 30),
                user_role=request.user_role
            )
        elif use_case_name == "parts_procurement":
            result = handlers.handle_parts_procurement(
                part_no=request.params.get("part_no"),
                required_qty=request.params.get("required_qty"),
                related_wo_id=request.params.get("related_wo_id"),
                needed_by=date.fromisoformat(request.params["needed_by"]) if "needed_by" in request.params else None,
                user_role=request.user_role
            )
        elif use_case_name == "availability_report":
            result = handlers.handle_availability_report(
                from_date=date.fromisoformat(request.params["from_date"]),
                to_date=date.fromisoformat(request.params["to_date"]),
                user_role=request.user_role
            )
        elif use_case_name == "vehicle_status":
            result = handlers.handle_vehicle_status_update(
                locomotive_id=request.params["locomotive_id"],
                status=request.params["status"],
                planned_workshop_id=request.params.get("planned_workshop_id"),
                user_role=request.user_role
            )
        elif use_case_name == "invoice_entry":
            result = handlers.handle_invoice_entry(
                invoice_number=request.params["invoice_number"],
                supplier=request.params["supplier"],
                amount=request.params["amount"],
                currency=request.params.get("currency", "EUR"),
                related_wo_id=request.params.get("related_wo_id"),
                user_role=request.user_role
            )
        elif use_case_name == "maintenance_task":
            result = handlers.handle_maintenance_task_creation(
                locomotive_id=request.params["locomotive_id"],
                task_type=request.params["task_type"],
                due_date=date.fromisoformat(request.params["due_date"]),
                workshop_id=request.params.get("workshop_id"),
                user_role=request.user_role
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown use case: {use_case_name}"
            )

        # Log as event
        event_store = EventStore(db)
        event_store.append_event(
            aggregate_type="FleetOneAgent",
            aggregate_id=f"use-case-{use_case_name}",
            event_type="UseCaseExecuted",
            data={
                "use_case": use_case_name,
                "params": request.params,
                "user_role": request.user_role,
                "success": result.success
            },
            metadata={"service": "fleet-one"}
        )
        db.commit()

        return {
            "use_case": use_case_name,
            "success": result.success,
            "message": result.message,
            "tool_calls": result.tool_calls,
            "data": result.data,
            "warnings": result.warnings,
            "suggestions": result.suggestions
        }

    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required parameter: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/metrics")
def get_agent_metrics():
    """Get FLEET-ONE agent performance metrics"""
    _ensure_initialized()

    # Return placeholder metrics
    # (Actual implementation would track metrics over time)
    return {
        "queries_total": 0,
        "queries_by_mode": {mode.value: 0 for mode in AgentMode},
        "avg_response_time_ms": 0.0,
        "success_rate": 1.0
    }


@router.get("/health")
def health_check():
    """FLEET-ONE agent health check"""
    try:
        _ensure_initialized()

        agent = get_agent()
        orchestrator = get_orchestrator()
        handlers = get_handlers()

        return {
            "status": "healthy",
            "service": "fleet-one",
            "version": agent.version if agent else "unknown",
            "components": {
                "agent": agent is not None,
                "orchestrator": orchestrator is not None,
                "handlers": handlers is not None
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
