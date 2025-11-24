"""Vehicle Projection - Read model for vehicles."""

from typing import List
from sqlalchemy.orm import Session

from .base import BaseProjection
from ...models.railfleet.events import Event as EventModel
from ...models.railfleet.vehicle import Vehicle, VehicleStatus
from ...config import get_logger

logger = get_logger(__name__)


class VehicleProjection(BaseProjection):
    """Projection for Vehicle aggregate.

    This projection maintains a denormalized view of vehicles
    by processing vehicle events.

    Handled Events:
    - VehicleCreatedEvent
    - VehicleUpdatedEvent
    - VehicleDeletedEvent
    - VehicleStatusChangedEvent
    - VehicleMileageUpdatedEvent
    """

    def get_handled_event_types(self) -> List[str]:
        """Return event types handled by this projection."""
        return [
            "VehicleCreatedEvent",
            "VehicleUpdatedEvent",
            "VehicleDeletedEvent",
            "VehicleStatusChangedEvent",
            "VehicleMileageUpdatedEvent",
        ]

    def handle_event(self, event: EventModel) -> None:
        """Process vehicle events.

        Args:
            event: The event to process
        """
        handler_map = {
            "VehicleCreatedEvent": self._handle_vehicle_created,
            "VehicleUpdatedEvent": self._handle_vehicle_updated,
            "VehicleDeletedEvent": self._handle_vehicle_deleted,
            "VehicleStatusChangedEvent": self._handle_status_changed,
            "VehicleMileageUpdatedEvent": self._handle_mileage_updated,
        }

        handler = handler_map.get(event.event_type)
        if handler:
            handler(event)

    def _handle_vehicle_created(self, event: EventModel) -> None:
        """Handle VehicleCreatedEvent.

        Args:
            event: The event
        """
        data = event.data

        # Check if vehicle already exists (idempotency)
        existing = self.db.query(Vehicle).filter(
            Vehicle.asset_id == event.aggregate_id
        ).first()

        if existing:
            logger.warning(f"Vehicle {event.aggregate_id} already exists, skipping create")
            return

        # Create new vehicle
        vehicle = Vehicle(
            asset_id=event.aggregate_id,
            model=data.get("model", "Unknown"),
            manufacturer=data.get("manufacturer", "Unknown"),
            build_year=data.get("build_year"),
            purchase_date=data.get("purchase_date"),
            status=VehicleStatus(data.get("status", "available")),
            current_mileage=data.get("current_mileage", 0),
            max_speed=data.get("max_speed"),
            power_output=data.get("power_output"),
            traction_type=data.get("traction_type"),
            created_at=event.occurred_at,
            updated_at=event.occurred_at,
        )

        self.db.add(vehicle)
        logger.info(f"Created vehicle projection: {event.aggregate_id}")

    def _handle_vehicle_updated(self, event: EventModel) -> None:
        """Handle VehicleUpdatedEvent.

        Args:
            event: The event
        """
        vehicle = self.db.query(Vehicle).filter(
            Vehicle.asset_id == event.aggregate_id
        ).first()

        if not vehicle:
            logger.warning(f"Vehicle {event.aggregate_id} not found for update")
            return

        # Update fields from event data
        data = event.data
        for field, value in data.items():
            if hasattr(vehicle, field):
                setattr(vehicle, field, value)

        vehicle.updated_at = event.occurred_at
        logger.info(f"Updated vehicle projection: {event.aggregate_id}")

    def _handle_vehicle_deleted(self, event: EventModel) -> None:
        """Handle VehicleDeletedEvent.

        Args:
            event: The event
        """
        vehicle = self.db.query(Vehicle).filter(
            Vehicle.asset_id == event.aggregate_id
        ).first()

        if vehicle:
            self.db.delete(vehicle)
            logger.info(f"Deleted vehicle projection: {event.aggregate_id}")

    def _handle_status_changed(self, event: EventModel) -> None:
        """Handle VehicleStatusChangedEvent.

        Args:
            event: The event
        """
        vehicle = self.db.query(Vehicle).filter(
            Vehicle.asset_id == event.aggregate_id
        ).first()

        if not vehicle:
            logger.warning(f"Vehicle {event.aggregate_id} not found for status change")
            return

        data = event.data
        old_status = data.get("old_status")
        new_status = data.get("new_status")

        vehicle.status = VehicleStatus(new_status)
        vehicle.updated_at = event.occurred_at

        logger.info(f"Updated vehicle {event.aggregate_id} status: {old_status} → {new_status}")

    def _handle_mileage_updated(self, event: EventModel) -> None:
        """Handle VehicleMileageUpdatedEvent.

        Args:
            event: The event
        """
        vehicle = self.db.query(Vehicle).filter(
            Vehicle.asset_id == event.aggregate_id
        ).first()

        if not vehicle:
            logger.warning(f"Vehicle {event.aggregate_id} not found for mileage update")
            return

        data = event.data
        old_mileage = data.get("old_mileage")
        new_mileage = data.get("new_mileage")

        vehicle.current_mileage = new_mileage
        vehicle.updated_at = event.occurred_at

        logger.info(f"Updated vehicle {event.aggregate_id} mileage: {old_mileage} → {new_mileage}")

    def reset(self) -> None:
        """Reset the vehicle projection (clear all vehicles)."""
        self.db.query(Vehicle).delete()
        self.db.commit()
        super().reset()
        logger.info("Vehicle projection reset complete")
