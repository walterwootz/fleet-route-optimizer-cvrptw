"""Audit Trail Service - Comprehensive audit logging and event replay.

Provides audit trail functionality, event replay for debugging,
and compliance reporting.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models.railfleet.events import Event as EventModel
from ..models.railfleet.event_log import EventLog
from ..config import get_logger

logger = get_logger(__name__)


class AuditEntry:
    """Single audit trail entry."""

    def __init__(
        self,
        timestamp: datetime,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        event_version: int,
        user_id: Optional[str],
        changes: Dict[str, Any],
        metadata: Dict[str, Any],
    ):
        self.timestamp = timestamp
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id
        self.event_type = event_type
        self.event_version = event_version
        self.user_id = user_id
        self.changes = changes
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "user_id": self.user_id,
            "changes": self.changes,
            "metadata": self.metadata,
        }


class AuditReport:
    """Audit report with statistics and findings."""

    def __init__(
        self,
        aggregate_type: str,
        aggregate_id: str,
        start_time: datetime,
        end_time: datetime,
    ):
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id
        self.start_time = start_time
        self.end_time = end_time
        self.entries: List[AuditEntry] = []
        self.statistics: Dict[str, Any] = {}
        self.findings: List[str] = []

    def add_entry(self, entry: AuditEntry):
        """Add audit entry to report."""
        self.entries.append(entry)

    def add_finding(self, finding: str):
        """Add audit finding."""
        self.findings.append(finding)

    def calculate_statistics(self):
        """Calculate audit statistics."""
        if not self.entries:
            self.statistics = {
                "total_events": 0,
                "unique_users": 0,
                "event_types": {},
            }
            return

        # Count events by type
        event_types = {}
        users = set()

        for entry in self.entries:
            event_types[entry.event_type] = event_types.get(entry.event_type, 0) + 1
            if entry.user_id:
                users.add(entry.user_id)

        self.statistics = {
            "total_events": len(self.entries),
            "unique_users": len(users),
            "event_types": event_types,
            "time_span_hours": (self.end_time - self.start_time).total_seconds() / 3600,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "entries": [entry.to_dict() for entry in self.entries],
            "statistics": self.statistics,
            "findings": self.findings,
        }


class EventReplay:
    """Event replay result."""

    def __init__(self):
        self.events_replayed: int = 0
        self.final_state: Dict[str, Any] = {}
        self.intermediate_states: List[Dict[str, Any]] = []
        self.errors: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "events_replayed": self.events_replayed,
            "final_state": self.final_state,
            "intermediate_states_count": len(self.intermediate_states),
            "errors": self.errors,
        }


class AuditTrailService:
    """Service for audit trail and event replay.

    Example:
        >>> audit = AuditTrailService(db)
        >>>
        >>> # Generate audit report
        >>> report = audit.generate_audit_report(
        ...     "Vehicle", "V001",
        ...     start_time=last_week,
        ...     end_time=now
        ... )
        >>> print(f"Total events: {report.statistics['total_events']}")
        >>>
        >>> # Replay events for debugging
        >>> replay = audit.replay_events("Vehicle", "V001")
        >>> print(f"Final state: {replay.final_state}")
        >>>
        >>> # Get user activity
        >>> activity = audit.get_user_activity("user123", last_month, now)
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_audit_report(
        self,
        aggregate_type: str,
        aggregate_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> AuditReport:
        """Generate comprehensive audit report for an aggregate.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier
            start_time: Start of audit period
            end_time: End of audit period

        Returns:
            AuditReport with entries, statistics, and findings
        """
        report = AuditReport(aggregate_type, aggregate_id, start_time, end_time)

        # Get all events in time range
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == aggregate_type,
                    EventModel.aggregate_id == aggregate_id,
                    EventModel.occurred_at >= start_time,
                    EventModel.occurred_at <= end_time,
                )
            )
            .order_by(EventModel.occurred_at)
            .all()
        )

        # Build audit entries
        for event in events:
            entry = AuditEntry(
                timestamp=event.occurred_at,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                event_version=event.aggregate_version,
                user_id=event.metadata.user_id if event.metadata else None,
                changes=event.data,
                metadata=event.metadata.to_dict() if event.metadata else {},
            )
            report.add_entry(entry)

        # Analyze for findings
        self._analyze_audit_trail(report)

        # Calculate statistics
        report.calculate_statistics()

        logger.info(
            f"Generated audit report for {aggregate_type}:{aggregate_id}: "
            f"{len(report.entries)} entries"
        )

        return report

    def replay_events(
        self,
        aggregate_type: str,
        aggregate_id: str,
        capture_intermediate: bool = False,
    ) -> EventReplay:
        """Replay all events for an aggregate to reconstruct state.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier
            capture_intermediate: Whether to capture intermediate states

        Returns:
            EventReplay with final state and optional intermediate states
        """
        replay = EventReplay()

        # Get all events
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == aggregate_type,
                    EventModel.aggregate_id == aggregate_id,
                )
            )
            .order_by(EventModel.aggregate_version)
            .all()
        )

        if not events:
            replay.errors.append(f"No events found for {aggregate_type}:{aggregate_id}")
            return replay

        # Replay events
        state = {}

        for event in events:
            try:
                # Apply event to state
                state = self._apply_event(state, event)

                # Capture intermediate state if requested
                if capture_intermediate:
                    replay.intermediate_states.append(state.copy())

                replay.events_replayed += 1

            except Exception as e:
                replay.errors.append(
                    f"Error replaying event {event.event_id}: {e}"
                )
                logger.error(f"Event replay error: {e}", exc_info=True)

        replay.final_state = state

        logger.info(
            f"Replayed {replay.events_replayed} events for {aggregate_type}:{aggregate_id}"
        )

        return replay

    def get_user_activity(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Get all activity for a user in time range.

        Args:
            user_id: User identifier
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum entries to return

        Returns:
            List of audit entries for user
        """
        # Query events by user
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.occurred_at >= start_time,
                    EventModel.occurred_at <= end_time,
                )
            )
            .order_by(EventModel.occurred_at.desc())
            .limit(limit)
            .all()
        )

        # Filter by user_id in metadata
        user_events = [
            event
            for event in events
            if event.metadata and event.metadata.user_id == user_id
        ]

        # Convert to audit entries
        entries = []
        for event in user_events:
            entry = AuditEntry(
                timestamp=event.occurred_at,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                event_version=event.aggregate_version,
                user_id=user_id,
                changes=event.data,
                metadata=event.metadata.to_dict() if event.metadata else {},
            )
            entries.append(entry)

        logger.info(f"Found {len(entries)} audit entries for user {user_id}")

        return entries

    def get_aggregate_timeline(
        self,
        aggregate_type: str,
        aggregate_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get timeline of changes for an aggregate.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier
            limit: Maximum timeline entries

        Returns:
            List of timeline entries with timestamp, event, and changes
        """
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == aggregate_type,
                    EventModel.aggregate_id == aggregate_id,
                )
            )
            .order_by(EventModel.occurred_at.desc())
            .limit(limit)
            .all()
        )

        timeline = []
        for event in events:
            entry = {
                "timestamp": event.occurred_at.isoformat(),
                "event_type": event.event_type,
                "version": event.aggregate_version,
                "user_id": event.metadata.user_id if event.metadata else None,
                "changes": event.data,
                "summary": self._generate_event_summary(event),
            }
            timeline.append(entry)

        return timeline

    def detect_anomalies(
        self,
        aggregate_type: str,
        aggregate_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in audit trail.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier
            start_time: Start of analysis period
            end_time: End of analysis period

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Get events
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == aggregate_type,
                    EventModel.aggregate_id == aggregate_id,
                    EventModel.occurred_at >= start_time,
                    EventModel.occurred_at <= end_time,
                )
            )
            .order_by(EventModel.occurred_at)
            .all()
        )

        # Check for rapid changes
        for i in range(1, len(events)):
            time_diff = (events[i].occurred_at - events[i - 1].occurred_at).total_seconds()

            if time_diff < 1:  # Less than 1 second between events
                anomalies.append({
                    "type": "rapid_changes",
                    "description": f"Two events within {time_diff:.2f} seconds",
                    "event_1": events[i - 1].event_id,
                    "event_2": events[i].event_id,
                    "timestamp": events[i].occurred_at.isoformat(),
                })

        # Check for missing versions
        for i in range(1, len(events)):
            version_diff = events[i].aggregate_version - events[i - 1].aggregate_version

            if version_diff > 1:
                anomalies.append({
                    "type": "missing_versions",
                    "description": f"Gap in versions: {events[i-1].aggregate_version} to {events[i].aggregate_version}",
                    "expected_versions": list(range(events[i-1].aggregate_version + 1, events[i].aggregate_version)),
                    "timestamp": events[i].occurred_at.isoformat(),
                })

        logger.info(f"Detected {len(anomalies)} anomalies in audit trail")

        return anomalies

    def _analyze_audit_trail(self, report: AuditReport):
        """Analyze audit trail for findings."""
        if not report.entries:
            return

        # Check for suspicious patterns
        if len(report.entries) > 100:
            report.add_finding(
                f"High number of events: {len(report.entries)} events in audit period"
            )

        # Check for events without user attribution
        no_user_count = sum(1 for entry in report.entries if not entry.user_id)
        if no_user_count > 0:
            report.add_finding(
                f"Found {no_user_count} events without user attribution"
            )

        # Check time gaps
        for i in range(1, len(report.entries)):
            time_gap = (
                report.entries[i].timestamp - report.entries[i - 1].timestamp
            ).total_seconds()

            if time_gap < 0.1:  # Less than 100ms
                report.add_finding(
                    f"Very rapid changes detected at {report.entries[i].timestamp}"
                )

    def _apply_event(self, state: Dict[str, Any], event: EventModel) -> Dict[str, Any]:
        """Apply event to state."""
        new_state = state.copy()

        if event.data:
            new_state.update(event.data)

        # Metadata
        new_state["_last_event"] = event.event_type
        new_state["_version"] = event.aggregate_version

        return new_state

    def _generate_event_summary(self, event: EventModel) -> str:
        """Generate human-readable event summary."""
        user = event.metadata.user_id if event.metadata else "Unknown"
        return f"{event.event_type} by {user}"
