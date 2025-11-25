"""
Enhanced sync service with event log and cursor-based pagination (WP8).
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime
from uuid import UUID
import uuid

from src.models.railfleet.maintenance import WorkOrder, SyncConflict
from src.models.railfleet.vehicle import Vehicle
from src.models.railfleet.transfer import TransferPlan, TransferAssignment
from src.models.railfleet.hr import Staff, StaffAssignment
from src.models.railfleet.docs import DocumentLink
from src.models.railfleet.event_log import EventLog


class EnhancedSyncService:
    """Enhanced offline-first synchronization with event log and cursor support."""

    # Supported entity types
    ENTITY_MODELS = {
        "work_order": WorkOrder,
        "vehicle": Vehicle,
        "transfer_plan": TransferPlan,
        "transfer_assignment": TransferAssignment,
        "staff": Staff,
        "staff_assignment": StaffAssignment,
        "document": DocumentLink,
    }

    def __init__(self, db: Session):
        self.db = db

    def process_push_events(
        self,
        events: List[Dict[str, Any]],
        device_id: str,
        actor_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Process push events from client and log to event_log.

        Args:
            events: List of sync events
            device_id: Client device ID
            actor_id: User performing the sync

        Returns:
            Dict with "applied", "conflicts", "rejected" event IDs and next_cursor
        """
        result = {"applied": [], "conflicts": [], "rejected": []}
        last_event_id = None

        for event in events:
            event_id = event.get("event_id") or event.get("id")
            try:
                # Check idempotency
                if self._is_duplicate_event(event.get("idempotency_key")):
                    result["applied"].append(event_id)
                    continue

                status, log_id = self._process_and_log_event(event, device_id, actor_id)
                result[status].append(event_id)

                if log_id:
                    last_event_id = log_id

            except Exception as e:
                print(f"Error processing event {event_id}: {e}")
                result["rejected"].append(event_id)

        self.db.commit()

        # Return cursor pointing to last event
        result["next_cursor"] = f"log-{last_event_id}" if last_event_id else None
        return result

    def pull_events(
        self,
        cursor: Optional[str] = None,
        limit: int = 100,
        entity_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Pull events from event log with cursor-based pagination.

        Args:
            cursor: Cursor in format "log-{id}" or None for start
            limit: Max events to return
            entity_types: Filter by entity types

        Returns:
            Dict with "events" list and "next_cursor"
        """
        query = self.db.query(EventLog).order_by(EventLog.id)

        # Apply cursor
        if cursor:
            try:
                cursor_id = int(cursor.split("-")[1])
                query = query.filter(EventLog.id > cursor_id)
            except (IndexError, ValueError):
                pass  # Invalid cursor, start from beginning

        # Filter by entity types
        if entity_types:
            query = query.filter(EventLog.entity_type.in_(entity_types))

        # Limit
        events = query.limit(limit).all()

        # Build response
        event_list = [
            {
                "event_id": e.event_id,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "event_type": e.event_type,
                "payload": e.payload_json,
                "actor_id": str(e.actor_id) if e.actor_id else None,
                "device_id": e.device_id,
                "source_ts": e.source_ts.isoformat() if e.source_ts else None,
                "server_ts": e.server_received_ts.isoformat() if e.server_received_ts else None,
            }
            for e in events
        ]

        # Next cursor
        next_cursor = f"log-{events[-1].id}" if events else cursor

        return {"events": event_list, "next_cursor": next_cursor, "has_more": len(events) == limit}

    def _process_and_log_event(
        self,
        event: Dict[str, Any],
        device_id: str,
        actor_id: Optional[UUID],
    ) -> tuple[str, Optional[int]]:
        """
        Process event and log to event_log.

        Returns:
            Tuple of (status: "applied"|"conflicts"|"rejected", event_log_id)
        """
        entity_type = event.get("entity_type")
        entity_id = event.get("entity_id")
        event_type = event.get("event_type", "updated")
        field_changes = event.get("field_changes") or event.get("payload", {})
        source_ts = event.get("source_ts") or event.get("timestamp")

        # Get entity
        entity = self._get_entity(entity_type, entity_id)
        if not entity and event_type != "created":
            return "rejected", None

        # Apply changes (simplified - real implementation would check permissions)
        has_conflict = False

        if event_type in ["updated", "created"]:
            for field, new_value in field_changes.items():
                if hasattr(entity, field):
                    # In real implementation, check role permissions here
                    setattr(entity, field, new_value)

        # Log to event_log
        event_log = EventLog(
            event_id=event.get("event_id") or f"evt-{uuid.uuid4().hex[:16]}",
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            payload_json=field_changes,
            actor_id=actor_id,
            device_id=device_id,
            source_ts=datetime.fromisoformat(source_ts) if isinstance(source_ts, str) else (source_ts or datetime.utcnow()),
            idempotency_key=event.get("idempotency_key"),
        )

        self.db.add(event_log)
        self.db.flush()  # Get event_log.id

        return ("conflicts" if has_conflict else "applied"), event_log.id

    def _get_entity(self, entity_type: str, entity_id: str):
        """Get entity by type and ID."""
        model = self.ENTITY_MODELS.get(entity_type)
        if not model:
            return None

        try:
            return self.db.query(model).filter(model.id == UUID(entity_id)).first()
        except Exception:
            return None

    def _is_duplicate_event(self, idempotency_key: Optional[str]) -> bool:
        """Check if event with idempotency key already exists."""
        if not idempotency_key:
            return False

        return (
            self.db.query(EventLog)
            .filter(EventLog.idempotency_key == idempotency_key)
            .first()
            is not None
        )

    def get_conflicts(
        self,
        entity_type: Optional[str] = None,
        resolved: bool = False,
    ) -> List[SyncConflict]:
        """Get conflicts, optionally filtered by entity type and resolved status."""
        query = self.db.query(SyncConflict)

        if entity_type:
            query = query.filter(SyncConflict.entity_type == entity_type)

        if not resolved:
            query = query.filter(SyncConflict.is_resolved == False)

        return query.order_by(desc(SyncConflict.created_at)).all()

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        custom_value: Any = None,
        user_id: Optional[str] = None,
    ) -> SyncConflict:
        """
        Resolve a conflict.

        Args:
            conflict_id: Conflict ID
            resolution: "server", "client", or "custom"
            custom_value: Custom value if resolution is "custom"
            user_id: ID of user resolving the conflict
        """
        conflict = (
            self.db.query(SyncConflict)
            .filter(SyncConflict.conflict_id == conflict_id)
            .first()
        )

        if not conflict:
            raise ValueError(f"Conflict {conflict_id} not found")

        if resolution == "server":
            resolved_value = conflict.server_value
        elif resolution == "client":
            resolved_value = conflict.client_value
        elif resolution == "custom":
            resolved_value = {"value": custom_value, "type": type(custom_value).__name__}
        else:
            raise ValueError(f"Invalid resolution: {resolution}")

        # Apply resolution to entity
        entity = self._get_entity(conflict.entity_type, conflict.entity_id)
        if entity:
            value = resolved_value.get("value") if isinstance(resolved_value, dict) else resolved_value
            setattr(entity, conflict.field_name, value)

            # Log resolution to event_log
            event_log = EventLog(
                event_id=f"conflict-resolve-{uuid.uuid4().hex[:16]}",
                entity_type=conflict.entity_type,
                entity_id=conflict.entity_id,
                event_type="conflict_resolved",
                payload_json={
                    "conflict_id": conflict_id,
                    "field": conflict.field_name,
                    "resolution": resolution,
                    "resolved_value": value,
                },
                actor_id=UUID(user_id) if user_id else None,
                device_id="server",
                source_ts=datetime.utcnow(),
            )
            self.db.add(event_log)

        # Update conflict record
        conflict.is_resolved = True
        conflict.resolved_value = resolved_value
        conflict.resolved_at = datetime.utcnow()
        if user_id:
            conflict.resolved_by = UUID(user_id)

        self.db.commit()
        return conflict

    def get_event_log_stats(self) -> Dict[str, Any]:
        """Get event log statistics."""
        total_events = self.db.query(EventLog).count()

        events_by_type = {}
        for entity_type in self.ENTITY_MODELS.keys():
            count = (
                self.db.query(EventLog)
                .filter(EventLog.entity_type == entity_type)
                .count()
            )
            if count > 0:
                events_by_type[entity_type] = count

        return {
            "total_events": total_events,
            "events_by_type": events_by_type,
            "supported_entity_types": list(self.ENTITY_MODELS.keys()),
        }
