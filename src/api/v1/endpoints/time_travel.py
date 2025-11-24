"""Time-Travel & Audit API Endpoints - WP19.

Provides HTTP endpoints for time-travel queries, audit trails,
change history, and compliance reporting.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ....models.database import get_db
from ....services.time_travel import TimeTravelQuery, TimePoint
from ....services.audit_trail import AuditTrailService
from ....services.change_history import ChangeHistoryService
from ....services.compliance_reporter import ComplianceReporter, ComplianceStandard
from ....config import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class TimePointRequest(BaseModel):
    """Request model for time point."""

    timestamp: Optional[datetime] = Field(None, description="Absolute timestamp")
    version: Optional[int] = Field(None, description="Version number")


class StateSnapshotResponse(BaseModel):
    """Response model for state snapshot."""

    aggregate_id: str
    aggregate_type: str
    state: dict
    version: int
    timestamp: datetime
    event_count: int


class CompareStatesRequest(BaseModel):
    """Request to compare states between two time points."""

    aggregate_type: str
    aggregate_id: str
    time_point_1: TimePointRequest
    time_point_2: TimePointRequest


class AuditReportRequest(BaseModel):
    """Request for audit report."""

    aggregate_type: str
    aggregate_id: str
    start_time: datetime
    end_time: datetime


class ComplianceReportRequest(BaseModel):
    """Request for compliance report."""

    standard: str = Field(..., description="gdpr, sox, iso27001, custom")
    start_date: datetime
    end_date: datetime
    scope: str = Field(default="all", description="Report scope")


# ============================================================================
# Time-Travel Endpoints
# ============================================================================


@router.get("/time-travel/{aggregate_type}/{aggregate_id}/at-timestamp")
def get_state_at_timestamp(
    aggregate_type: str,
    aggregate_id: str,
    timestamp: datetime = Query(..., description="Timestamp to query"),
    db: Session = Depends(get_db),
):
    """Get entity state at a specific timestamp.

    Args:
        aggregate_type: Type of aggregate (Vehicle, WorkOrder, etc.)
        aggregate_id: Aggregate identifier
        timestamp: Point in time to query
        db: Database session

    Returns:
        State snapshot at that time
    """
    query = TimeTravelQuery(db)
    time_point = TimePoint.at_timestamp(timestamp)

    snapshot = query.get_state_at(aggregate_type, aggregate_id, time_point)

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No state found for {aggregate_type}:{aggregate_id} at {timestamp}",
        )

    return snapshot.to_dict()


@router.get("/time-travel/{aggregate_type}/{aggregate_id}/at-version")
def get_state_at_version(
    aggregate_type: str,
    aggregate_id: str,
    version: int = Query(..., description="Version number to query", ge=0),
    db: Session = Depends(get_db),
):
    """Get entity state at a specific version.

    Args:
        aggregate_type: Type of aggregate
        aggregate_id: Aggregate identifier
        version: Version number to query
        db: Database session

    Returns:
        State snapshot at that version
    """
    query = TimeTravelQuery(db)
    time_point = TimePoint.at_version(version)

    snapshot = query.get_state_at(aggregate_type, aggregate_id, time_point)

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No state found for {aggregate_type}:{aggregate_id} at version {version}",
        )

    return snapshot.to_dict()


@router.get("/time-travel/{aggregate_type}/{aggregate_id}/history")
def get_state_history(
    aggregate_type: str,
    aggregate_id: str,
    start_time: Optional[datetime] = Query(None, description="Start of time range"),
    end_time: Optional[datetime] = Query(None, description="End of time range"),
    limit: int = Query(100, ge=1, le=500, description="Max snapshots"),
    db: Session = Depends(get_db),
):
    """Get state history with snapshots at each event.

    Args:
        aggregate_type: Type of aggregate
        aggregate_id: Aggregate identifier
        start_time: Optional start time
        end_time: Optional end time
        limit: Maximum snapshots
        db: Database session

    Returns:
        List of state snapshots showing evolution
    """
    query = TimeTravelQuery(db)

    snapshots = query.get_state_history(
        aggregate_type, aggregate_id, start_time, end_time, limit
    )

    return {
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "snapshots": [s.to_dict() for s in snapshots],
        "count": len(snapshots),
    }


@router.post("/time-travel/compare")
def compare_states(
    request: CompareStatesRequest,
    db: Session = Depends(get_db),
):
    """Compare entity state between two points in time.

    Args:
        request: Comparison request with two time points
        db: Database session

    Returns:
        Differences between states
    """
    query = TimeTravelQuery(db)

    # Create time points
    tp1 = TimePoint(
        timestamp=request.time_point_1.timestamp,
        version=request.time_point_1.version,
    )
    tp2 = TimePoint(
        timestamp=request.time_point_2.timestamp,
        version=request.time_point_2.version,
    )

    comparison = query.compare_states(
        request.aggregate_type, request.aggregate_id, tp1, tp2
    )

    return comparison


@router.get("/time-travel/{aggregate_type}/{aggregate_id}/events-between")
def get_events_between(
    aggregate_type: str,
    aggregate_id: str,
    start_time: datetime = Query(..., description="Start timestamp"),
    end_time: datetime = Query(..., description="End timestamp"),
    db: Session = Depends(get_db),
):
    """Get all events for an aggregate between two timestamps.

    Args:
        aggregate_type: Type of aggregate
        aggregate_id: Aggregate identifier
        start_time: Start timestamp
        end_time: End timestamp
        db: Database session

    Returns:
        List of events in time range
    """
    query = TimeTravelQuery(db)

    events = query.get_events_between(
        aggregate_type, aggregate_id, start_time, end_time
    )

    return {
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "events": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "version": e.aggregate_version,
                "occurred_at": e.occurred_at.isoformat(),
                "data": e.data,
            }
            for e in events
        ],
        "count": len(events),
    }


# ============================================================================
# Audit Trail Endpoints
# ============================================================================


@router.post("/audit/report")
def generate_audit_report(
    request: AuditReportRequest,
    db: Session = Depends(get_db),
):
    """Generate comprehensive audit report for an aggregate.

    Args:
        request: Audit report request
        db: Database session

    Returns:
        Audit report with entries, statistics, and findings
    """
    audit_service = AuditTrailService(db)

    report = audit_service.generate_audit_report(
        request.aggregate_type,
        request.aggregate_id,
        request.start_time,
        request.end_time,
    )

    return report.to_dict()


@router.get("/audit/{aggregate_type}/{aggregate_id}/replay")
def replay_events(
    aggregate_type: str,
    aggregate_id: str,
    capture_intermediate: bool = Query(
        False, description="Capture intermediate states"
    ),
    db: Session = Depends(get_db),
):
    """Replay all events for an aggregate to reconstruct state.

    Args:
        aggregate_type: Type of aggregate
        aggregate_id: Aggregate identifier
        capture_intermediate: Whether to capture intermediate states
        db: Database session

    Returns:
        Event replay result with final state
    """
    audit_service = AuditTrailService(db)

    replay = audit_service.replay_events(
        aggregate_type, aggregate_id, capture_intermediate
    )

    return replay.to_dict()


@router.get("/audit/user/{user_id}/activity")
def get_user_activity(
    user_id: str,
    start_time: datetime = Query(..., description="Start of time range"),
    end_time: datetime = Query(..., description="End of time range"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get all activity for a user in time range.

    Args:
        user_id: User identifier
        start_time: Start of time range
        end_time: End of time range
        limit: Maximum entries
        db: Database session

    Returns:
        List of audit entries for user
    """
    audit_service = AuditTrailService(db)

    entries = audit_service.get_user_activity(user_id, start_time, end_time, limit)

    return {
        "user_id": user_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "entries": [e.to_dict() for e in entries],
        "count": len(entries),
    }


@router.get("/audit/{aggregate_type}/{aggregate_id}/timeline")
def get_aggregate_timeline(
    aggregate_type: str,
    aggregate_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get timeline of changes for an aggregate.

    Args:
        aggregate_type: Type of aggregate
        aggregate_id: Aggregate identifier
        limit: Maximum timeline entries
        db: Database session

    Returns:
        Timeline entries with timestamp, event, and changes
    """
    audit_service = AuditTrailService(db)

    timeline = audit_service.get_aggregate_timeline(
        aggregate_type, aggregate_id, limit
    )

    return {
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "timeline": timeline,
        "count": len(timeline),
    }


@router.get("/audit/{aggregate_type}/{aggregate_id}/anomalies")
def detect_anomalies(
    aggregate_type: str,
    aggregate_id: str,
    start_time: datetime = Query(..., description="Start of analysis period"),
    end_time: datetime = Query(..., description="End of analysis period"),
    db: Session = Depends(get_db),
):
    """Detect anomalies in audit trail.

    Args:
        aggregate_type: Type of aggregate
        aggregate_id: Aggregate identifier
        start_time: Start of analysis period
        end_time: End of analysis period
        db: Database session

    Returns:
        List of detected anomalies
    """
    audit_service = AuditTrailService(db)

    anomalies = audit_service.detect_anomalies(
        aggregate_type, aggregate_id, start_time, end_time
    )

    return {
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "anomalies": anomalies,
        "count": len(anomalies),
    }


# ============================================================================
# Change History Endpoints
# ============================================================================


@router.get("/changes/{aggregate_type}/{aggregate_id}/history")
def get_change_history(
    aggregate_type: str,
    aggregate_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """Get complete change history for an entity.

    Args:
        aggregate_type: Type of aggregate
        aggregate_id: Aggregate identifier
        start_time: Optional start time
        end_time: Optional end time
        db: Database session

    Returns:
        Change history with all changesets
    """
    change_service = ChangeHistoryService(db)

    history = change_service.get_change_history(
        aggregate_type, aggregate_id, start_time, end_time
    )

    return history.to_dict()


@router.get("/changes/{aggregate_type}/{aggregate_id}/field/{field_name}")
def get_field_history(
    aggregate_type: str,
    aggregate_id: str,
    field_name: str,
    db: Session = Depends(get_db),
):
    """Get history of changes for a specific field.

    Args:
        aggregate_type: Type of aggregate
        aggregate_id: Aggregate identifier
        field_name: Name of field to track
        db: Database session

    Returns:
        List of field changes
    """
    change_service = ChangeHistoryService(db)

    field_changes = change_service.get_field_history(
        aggregate_type, aggregate_id, field_name
    )

    return {
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "field_name": field_name,
        "changes": [c.to_dict() for c in field_changes],
        "count": len(field_changes),
    }


@router.get("/changes/{aggregate_type}/{aggregate_id}/recent")
def get_recent_changes(
    aggregate_type: str,
    aggregate_id: str,
    hours: int = Query(24, ge=1, le=720, description="Hours to look back"),
    db: Session = Depends(get_db),
):
    """Get recent changes within specified hours.

    Args:
        aggregate_type: Type of aggregate
        aggregate_id: Aggregate identifier
        hours: Number of hours to look back
        db: Database session

    Returns:
        Recent change history
    """
    change_service = ChangeHistoryService(db)

    history = change_service.get_recent_changes(aggregate_type, aggregate_id, hours)

    return history.to_dict()


@router.get("/changes/{aggregate_type}/{aggregate_id}/compare-versions")
def compare_versions(
    aggregate_type: str,
    aggregate_id: str,
    version_1: int = Query(..., ge=0),
    version_2: int = Query(..., ge=0),
    db: Session = Depends(get_db),
):
    """Compare two versions and return field changes.

    Args:
        aggregate_type: Type of aggregate
        aggregate_id: Aggregate identifier
        version_1: First version number
        version_2: Second version number
        db: Database session

    Returns:
        List of field changes between versions
    """
    change_service = ChangeHistoryService(db)

    changes = change_service.compare_versions(
        aggregate_type, aggregate_id, version_1, version_2
    )

    return {
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "version_1": version_1,
        "version_2": version_2,
        "changes": [c.to_dict() for c in changes],
        "count": len(changes),
    }


@router.get("/changes/{aggregate_type}/{aggregate_id}/who-changed-what")
def get_who_changed_what(
    aggregate_type: str,
    aggregate_id: str,
    db: Session = Depends(get_db),
):
    """Get mapping of users to fields they changed.

    Args:
        aggregate_type: Type of aggregate
        aggregate_id: Aggregate identifier
        db: Database session

    Returns:
        Dictionary mapping user_id to list of fields changed
    """
    change_service = ChangeHistoryService(db)

    user_changes = change_service.get_who_changed_what(aggregate_type, aggregate_id)

    return {
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "user_changes": user_changes,
    }


# ============================================================================
# Compliance Endpoints
# ============================================================================


@router.post("/compliance/gdpr-report")
def generate_gdpr_report(
    request: ComplianceReportRequest,
    db: Session = Depends(get_db),
):
    """Generate GDPR compliance report.

    Args:
        request: Compliance report request
        db: Database session

    Returns:
        GDPR compliance report
    """
    reporter = ComplianceReporter(db)

    report = reporter.generate_gdpr_report(
        request.start_date, request.end_date, request.scope
    )

    return report.to_dict()


@router.post("/compliance/sox-report")
def generate_sox_report(
    request: ComplianceReportRequest,
    db: Session = Depends(get_db),
):
    """Generate SOX compliance report.

    Args:
        request: Compliance report request
        db: Database session

    Returns:
        SOX compliance report
    """
    reporter = ComplianceReporter(db)

    report = reporter.generate_sox_report(
        request.start_date, request.end_date, request.scope
    )

    return report.to_dict()


@router.get("/compliance/activity-summary")
def get_activity_summary(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: Session = Depends(get_db),
):
    """Generate activity summary for compliance.

    Args:
        start_date: Start of period
        end_date: End of period
        db: Database session

    Returns:
        Activity statistics
    """
    reporter = ComplianceReporter(db)

    summary = reporter.generate_activity_summary(start_date, end_date)

    return summary
