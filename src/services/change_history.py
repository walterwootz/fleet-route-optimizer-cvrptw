"""Change History Service - Detailed change tracking and diff generation.

Tracks all changes to entities with field-level granularity and
generates human-readable diffs.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.railfleet.events import Event as EventModel
from ..config import get_logger

logger = get_logger(__name__)


class ChangeType(str, Enum):
    """Type of change."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ADDED = "added"  # For collection items
    REMOVED = "removed"  # For collection items


class FieldChange:
    """Represents a change to a single field."""

    def __init__(
        self,
        field_name: str,
        change_type: ChangeType,
        old_value: Any,
        new_value: Any,
        timestamp: datetime,
        user_id: Optional[str] = None,
    ):
        self.field_name = field_name
        self.change_type = change_type
        self.old_value = old_value
        self.new_value = new_value
        self.timestamp = timestamp
        self.user_id = user_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field_name": self.field_name,
            "change_type": self.change_type.value,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
        }

    def to_human_readable(self) -> str:
        """Generate human-readable change description."""
        if self.change_type == ChangeType.CREATED:
            return f"{self.field_name} created with value '{self.new_value}'"
        elif self.change_type == ChangeType.UPDATED:
            return f"{self.field_name} changed from '{self.old_value}' to '{self.new_value}'"
        elif self.change_type == ChangeType.DELETED:
            return f"{self.field_name} deleted (was '{self.old_value}')"
        elif self.change_type == ChangeType.ADDED:
            return f"Added '{self.new_value}' to {self.field_name}"
        elif self.change_type == ChangeType.REMOVED:
            return f"Removed '{self.old_value}' from {self.field_name}"
        return f"{self.field_name}: {self.change_type.value}"


class ChangeSet:
    """Set of changes at a specific point in time."""

    def __init__(
        self,
        timestamp: datetime,
        event_type: str,
        version: int,
        user_id: Optional[str] = None,
    ):
        self.timestamp = timestamp
        self.event_type = event_type
        self.version = version
        self.user_id = user_id
        self.field_changes: List[FieldChange] = []

    def add_change(self, change: FieldChange):
        """Add a field change to this changeset."""
        self.field_changes.append(change)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "version": self.version,
            "user_id": self.user_id,
            "field_changes": [change.to_dict() for change in self.field_changes],
            "change_count": len(self.field_changes),
        }

    def to_human_readable(self) -> str:
        """Generate human-readable changeset description."""
        changes_desc = "\n  - ".join(
            change.to_human_readable() for change in self.field_changes
        )
        user_desc = f" by {self.user_id}" if self.user_id else ""
        return (
            f"Changes at {self.timestamp.isoformat()}{user_desc}:\n"
            f"  - {changes_desc}"
        )


class ChangeHistory:
    """Complete change history for an entity."""

    def __init__(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ):
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id
        self.changesets: List[ChangeSet] = []
        self.summary: Dict[str, Any] = {}

    def add_changeset(self, changeset: ChangeSet):
        """Add a changeset to history."""
        self.changesets.append(changeset)

    def calculate_summary(self):
        """Calculate summary statistics."""
        if not self.changesets:
            self.summary = {
                "total_changesets": 0,
                "total_field_changes": 0,
                "unique_fields_changed": set(),
                "unique_users": set(),
            }
            return

        unique_fields = set()
        unique_users = set()
        total_field_changes = 0

        for changeset in self.changesets:
            total_field_changes += len(changeset.field_changes)
            if changeset.user_id:
                unique_users.add(changeset.user_id)

            for change in changeset.field_changes:
                unique_fields.add(change.field_name)

        self.summary = {
            "total_changesets": len(self.changesets),
            "total_field_changes": total_field_changes,
            "unique_fields_changed": list(unique_fields),
            "unique_users": list(unique_users),
            "first_change": self.changesets[0].timestamp.isoformat() if self.changesets else None,
            "last_change": self.changesets[-1].timestamp.isoformat() if self.changesets else None,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "changesets": [cs.to_dict() for cs in self.changesets],
            "summary": self.summary,
        }


class ChangeHistoryService:
    """Service for tracking and analyzing change history.

    Example:
        >>> tracker = ChangeHistoryService(db)
        >>>
        >>> # Get complete change history
        >>> history = tracker.get_change_history("Vehicle", "V001")
        >>> print(f"Total changes: {history.summary['total_field_changes']}")
        >>>
        >>> # Get changes for specific field
        >>> field_history = tracker.get_field_history(
        ...     "Vehicle", "V001", "status"
        ... )
        >>>
        >>> # Get recent changes
        >>> recent = tracker.get_recent_changes(
        ...     "Vehicle", "V001", hours=24
        ... )
    """

    def __init__(self, db: Session):
        self.db = db

    def get_change_history(
        self,
        aggregate_type: str,
        aggregate_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> ChangeHistory:
        """Get complete change history for an entity.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            ChangeHistory with all changesets
        """
        history = ChangeHistory(aggregate_type, aggregate_id)

        # Get events
        query = self.db.query(EventModel).filter(
            and_(
                EventModel.aggregate_type == aggregate_type,
                EventModel.aggregate_id == aggregate_id,
            )
        )

        if start_time:
            query = query.filter(EventModel.occurred_at >= start_time)
        if end_time:
            query = query.filter(EventModel.occurred_at <= end_time)

        events = query.order_by(EventModel.aggregate_version).all()

        # Build changesets with field-level diffs
        previous_state = {}

        for event in events:
            changeset = ChangeSet(
                timestamp=event.occurred_at,
                event_type=event.event_type,
                version=event.aggregate_version,
                user_id=event.metadata.user_id if event.metadata else None,
            )

            # Calculate field changes
            if event.data:
                field_changes = self._calculate_field_changes(
                    previous_state,
                    event.data,
                    event.occurred_at,
                    event.metadata.user_id if event.metadata else None,
                )

                for change in field_changes:
                    changeset.add_change(change)

                # Update previous state
                previous_state.update(event.data)

            history.add_changeset(changeset)

        # Calculate summary
        history.calculate_summary()

        logger.info(
            f"Retrieved change history for {aggregate_type}:{aggregate_id}: "
            f"{len(history.changesets)} changesets"
        )

        return history

    def get_field_history(
        self,
        aggregate_type: str,
        aggregate_id: str,
        field_name: str,
    ) -> List[FieldChange]:
        """Get history of changes for a specific field.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier
            field_name: Name of field to track

        Returns:
            List of FieldChange objects for the field
        """
        history = self.get_change_history(aggregate_type, aggregate_id)

        # Extract changes for specific field
        field_changes = []
        for changeset in history.changesets:
            for change in changeset.field_changes:
                if change.field_name == field_name:
                    field_changes.append(change)

        logger.info(
            f"Found {len(field_changes)} changes for field {field_name} "
            f"on {aggregate_type}:{aggregate_id}"
        )

        return field_changes

    def get_recent_changes(
        self,
        aggregate_type: str,
        aggregate_id: str,
        hours: int = 24,
    ) -> ChangeHistory:
        """Get recent changes within specified hours.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier
            hours: Number of hours to look back

        Returns:
            ChangeHistory with recent changesets
        """
        from datetime import timedelta

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        return self.get_change_history(
            aggregate_type, aggregate_id, start_time, end_time
        )

    def compare_versions(
        self,
        aggregate_type: str,
        aggregate_id: str,
        version_1: int,
        version_2: int,
    ) -> List[FieldChange]:
        """Compare two versions and return field changes.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier
            version_1: First version number
            version_2: Second version number

        Returns:
            List of FieldChange objects between versions
        """
        # Get events at both versions
        event_1 = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == aggregate_type,
                    EventModel.aggregate_id == aggregate_id,
                    EventModel.aggregate_version == version_1,
                )
            )
            .first()
        )

        event_2 = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == aggregate_type,
                    EventModel.aggregate_id == aggregate_id,
                    EventModel.aggregate_version == version_2,
                )
            )
            .first()
        )

        if not event_1 or not event_2:
            logger.warning(
                f"Could not find events for versions {version_1} and {version_2}"
            )
            return []

        # Calculate field changes
        changes = self._calculate_field_changes(
            event_1.data or {},
            event_2.data or {},
            event_2.occurred_at,
            event_2.metadata.user_id if event_2.metadata else None,
        )

        return changes

    def get_who_changed_what(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> Dict[str, List[str]]:
        """Get mapping of users to fields they changed.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier

        Returns:
            Dictionary mapping user_id to list of fields changed
        """
        history = self.get_change_history(aggregate_type, aggregate_id)

        user_changes: Dict[str, set] = {}

        for changeset in history.changesets:
            if not changeset.user_id:
                continue

            if changeset.user_id not in user_changes:
                user_changes[changeset.user_id] = set()

            for change in changeset.field_changes:
                user_changes[changeset.user_id].add(change.field_name)

        # Convert sets to lists
        return {
            user: list(fields) for user, fields in user_changes.items()
        }

    def _calculate_field_changes(
        self,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        timestamp: datetime,
        user_id: Optional[str],
    ) -> List[FieldChange]:
        """Calculate field-level changes between two states."""
        changes = []

        # Get all fields
        all_fields = set(old_state.keys()) | set(new_state.keys())

        for field in all_fields:
            old_value = old_state.get(field)
            new_value = new_state.get(field)

            # Determine change type
            if old_value is None and new_value is not None:
                change_type = ChangeType.CREATED
            elif old_value is not None and new_value is None:
                change_type = ChangeType.DELETED
            elif old_value != new_value:
                change_type = ChangeType.UPDATED
            else:
                continue  # No change

            change = FieldChange(
                field_name=field,
                change_type=change_type,
                old_value=old_value,
                new_value=new_value,
                timestamp=timestamp,
                user_id=user_id,
            )
            changes.append(change)

        return changes
