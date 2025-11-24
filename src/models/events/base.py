"""Base Event Sourcing Classes."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class EventMetadata(BaseModel):
    """Metadata for events."""

    user_id: Optional[str] = None
    user_email: Optional[str] = None
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    causation_id: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        frozen = True


class BaseEvent(BaseModel, ABC):
    """Base class for all domain events.

    Events are immutable records of things that have happened in the system.
    They follow the Event Sourcing pattern where the state is derived from
    the sequence of events rather than storing current state directly.
    """

    # Event identity
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(default="")
    event_version: int = Field(default=1, ge=1)

    # Aggregate identity
    aggregate_id: str
    aggregate_type: str
    aggregate_version: int = Field(default=0, ge=0)

    # Timestamps
    occurred_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    # Event data (specific to each event type)
    data: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data):
        super().__init__(**data)
        # Auto-set event_type from class name if not provided
        if not self.event_type:
            object.__setattr__(self, 'event_type', self.__class__.__name__)

    class Config:
        frozen = True  # Events are immutable
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage."""
        return self.dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseEvent":
        """Reconstruct event from dictionary."""
        return cls(**data)

    def with_metadata(self, **kwargs) -> "BaseEvent":
        """Create a new event with updated metadata."""
        metadata_dict = self.metadata.dict()
        metadata_dict.update(kwargs)
        new_metadata = EventMetadata(**metadata_dict)

        event_dict = self.dict()
        event_dict['metadata'] = new_metadata
        return self.__class__(**event_dict)


EventType = TypeVar('EventType', bound=BaseEvent)


class AggregateRoot(ABC):
    """Base class for aggregate roots in Domain-Driven Design.

    Aggregates are clusters of domain objects that can be treated as a single unit.
    The aggregate root is the only object that external objects can reference.

    In Event Sourcing, aggregates are reconstituted from their event history.
    """

    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.aggregate_type = self.__class__.__name__
        self.version = 0
        self._uncommitted_events: List[BaseEvent] = []

    def apply_event(self, event: BaseEvent, is_new: bool = True) -> None:
        """Apply an event to update the aggregate state.

        Args:
            event: The event to apply
            is_new: Whether this is a new event (True) or being replayed (False)
        """
        # Find the handler method for this event type
        handler_name = f"_apply_{event.event_type}"
        handler = getattr(self, handler_name, None)

        if handler:
            handler(event)
        else:
            # Default behavior: just increment version
            pass

        # Increment version
        self.version = event.aggregate_version

        # If this is a new event, add to uncommitted events
        if is_new:
            self._uncommitted_events.append(event)

    def get_uncommitted_events(self) -> List[BaseEvent]:
        """Get events that haven't been persisted yet."""
        return self._uncommitted_events.copy()

    def clear_uncommitted_events(self) -> None:
        """Clear uncommitted events after they've been persisted."""
        self._uncommitted_events.clear()

    def load_from_history(self, events: List[BaseEvent]) -> None:
        """Reconstitute aggregate from event history.

        Args:
            events: List of events in chronological order
        """
        for event in events:
            self.apply_event(event, is_new=False)

    @abstractmethod
    def _apply_default(self, event: BaseEvent) -> None:
        """Default event application handler.

        This is called when no specific handler is found for an event type.
        """
        pass

    def create_event(
        self,
        event_class: Type[EventType],
        data: Dict[str, Any],
        metadata: Optional[EventMetadata] = None
    ) -> EventType:
        """Create a new event for this aggregate.

        Args:
            event_class: The event class to instantiate
            data: Event-specific data
            metadata: Optional metadata for the event

        Returns:
            The created event
        """
        if metadata is None:
            metadata = EventMetadata()

        event = event_class(
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type,
            aggregate_version=self.version + 1,
            metadata=metadata,
            data=data
        )

        return event

    def raise_event(
        self,
        event_class: Type[EventType],
        data: Dict[str, Any],
        metadata: Optional[EventMetadata] = None
    ) -> EventType:
        """Create and apply a new event.

        This is the main method for creating new events in the system.

        Args:
            event_class: The event class to instantiate
            data: Event-specific data
            metadata: Optional metadata for the event

        Returns:
            The created and applied event
        """
        event = self.create_event(event_class, data, metadata)
        self.apply_event(event, is_new=True)
        return event


class Snapshot(BaseModel):
    """Snapshot of aggregate state for performance optimization.

    Snapshots allow reconstructing aggregates without replaying all events.
    """

    snapshot_id: str = Field(default_factory=lambda: str(uuid4()))
    aggregate_id: str
    aggregate_type: str
    aggregate_version: int
    state: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
