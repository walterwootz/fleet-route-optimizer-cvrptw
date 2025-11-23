"""
Sync service for offline-first synchronization with conflict detection.
"""
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from src.models.railfleet.maintenance import WorkOrder, SyncConflict
from src.models.railfleet.vehicle import Vehicle
from src.policy.loader import get_policy_loader


class SyncService:
    """Handles offline-first synchronization with conflict detection."""

    def __init__(self, db: Session):
        self.db = db
        self.policy_loader = get_policy_loader()

    def process_push_events(
        self, events: List[Dict[str, Any]], device_id: str
    ) -> Dict[str, List[str]]:
        """
        Process push events from client.

        Args:
            events: List of sync events
            device_id: Client device ID

        Returns:
            Dict with "applied", "conflicts", and "rejected" event IDs
        """
        result = {"applied": [], "conflicts": [], "rejected": []}

        for event in events:
            event_id = event.get("id")
            try:
                status = self._process_single_event(event, device_id)
                result[status].append(event_id)
            except Exception as e:
                print(f"Error processing event {event_id}: {e}")
                result["rejected"].append(event_id)

        self.db.commit()
        return result

    def _process_single_event(
        self, event: Dict[str, Any], device_id: str
    ) -> str:
        """
        Process a single sync event.

        Returns:
            "applied", "conflicts", or "rejected"
        """
        entity_type = event.get("entity_type")
        entity_id = event.get("entity_id")
        field_changes = event.get("field_changes", {})
        source_role = event.get("source_role")

        # Get entity
        entity = self._get_entity(entity_type, entity_id)
        if not entity:
            return "rejected"

        # Process each field change
        has_conflict = False

        for field, new_value in field_changes.items():
            # Check if role can update field
            if not self.policy_loader.can_role_update_field(source_role, field):
                self._create_conflict(
                    entity_type,
                    entity_id,
                    field,
                    getattr(entity, field, None),
                    new_value,
                    source_role,
                    device_id,
                    f"Role {source_role} not authorized to update {field}",
                )
                has_conflict = True
                continue

            # Get current value
            current_value = getattr(entity, field, None)

            # Resolve conflict using policy
            resolution = self.policy_loader.resolve_conflict(
                field, current_value, new_value, source_role
            )

            if resolution["action"] == "accept":
                # Apply change
                setattr(entity, field, new_value)

            elif resolution["action"] == "flag_conflict":
                # Create conflict record
                self._create_conflict(
                    entity_type,
                    entity_id,
                    field,
                    current_value,
                    new_value,
                    source_role,
                    device_id,
                    resolution["reason"],
                )
                has_conflict = True

            elif resolution["action"] == "reject":
                has_conflict = True

        if has_conflict:
            return "conflicts"
        else:
            return "applied"

    def _get_entity(self, entity_type: str, entity_id: str):
        """Get entity by type and ID."""
        try:
            if entity_type == "work_order":
                return self.db.query(WorkOrder).filter(WorkOrder.id == UUID(entity_id)).first()
            elif entity_type == "vehicle":
                return self.db.query(Vehicle).filter(Vehicle.id == UUID(entity_id)).first()
            return None
        except Exception:
            return None

    def _create_conflict(
        self,
        entity_type: str,
        entity_id: str,
        field_name: str,
        server_value: Any,
        client_value: Any,
        source_role: str,
        device_id: str,
        reason: str,
    ):
        """Create a conflict record."""
        import uuid

        conflict_id = f"CONFLICT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

        conflict = SyncConflict(
            conflict_id=conflict_id,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            server_value={"value": server_value, "type": type(server_value).__name__},
            client_value={"value": client_value, "type": type(client_value).__name__},
            source_device=device_id,
            source_role=source_role,
        )

        self.db.add(conflict)

    def get_conflicts(self, resolved: bool = False) -> List[SyncConflict]:
        """Get all conflicts, optionally filtered by resolved status."""
        query = self.db.query(SyncConflict)

        if not resolved:
            query = query.filter(SyncConflict.is_resolved == False)

        return query.all()

    def resolve_conflict(
        self, conflict_id: str, resolution: str, custom_value: Any = None, user_id: str = None
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
            raise ValueError("Conflict not found")

        if resolution == "server":
            resolved_value = conflict.server_value
        elif resolution == "client":
            resolved_value = conflict.client_value
        elif resolution == "custom":
            resolved_value = custom_value
        else:
            raise ValueError("Invalid resolution")

        # Apply resolution to entity
        entity = self._get_entity(conflict.entity_type, conflict.entity_id)
        if entity:
            setattr(entity, conflict.field_name, resolved_value.get("value"))

        # Update conflict record
        conflict.is_resolved = True
        conflict.resolved_value = resolved_value
        conflict.resolved_at = datetime.utcnow()
        if user_id:
            conflict.resolved_by = UUID(user_id)

        self.db.commit()
        return conflict
