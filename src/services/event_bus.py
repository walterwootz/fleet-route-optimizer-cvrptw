"""Event Bus for publishing and subscribing to domain events."""

from typing import Callable, Dict, List, Type, Any
from collections import defaultdict
import asyncio
from datetime import datetime

from ..models.events.base import BaseEvent
from ..config import get_logger

logger = get_logger(__name__)


EventHandler = Callable[[BaseEvent], None]
AsyncEventHandler = Callable[[BaseEvent], Any]


class EventBus:
    """Event Bus for event-driven architecture.

    The Event Bus allows components to subscribe to events and be notified
    when events occur. This enables loose coupling and reactive behavior.

    Supports both synchronous and asynchronous event handlers.
    """

    def __init__(self):
        # Synchronous handlers: event_type -> List[handler]
        self._sync_handlers: Dict[str, List[EventHandler]] = defaultdict(list)

        # Asynchronous handlers: event_type -> List[async_handler]
        self._async_handlers: Dict[str, List[AsyncEventHandler]] = defaultdict(list)

        # Wildcard handlers (receive all events)
        self._wildcard_sync_handlers: List[EventHandler] = []
        self._wildcard_async_handlers: List[AsyncEventHandler] = []

        # Event history (for debugging)
        self._published_events: List[BaseEvent] = []
        self._max_history = 1000

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        is_async: bool = False
    ) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: The type of event to subscribe to (e.g., 'VehicleCreatedEvent')
            handler: The handler function to call when event occurs
            is_async: Whether the handler is async (default: False)
        """
        if is_async:
            self._async_handlers[event_type].append(handler)
        else:
            self._sync_handlers[event_type].append(handler)

        logger.info(f"Subscribed {'async' if is_async else 'sync'} handler to {event_type}")

    def subscribe_all(
        self,
        handler: EventHandler,
        is_async: bool = False
    ) -> None:
        """Subscribe to all events (wildcard subscription).

        Args:
            handler: The handler function to call for all events
            is_async: Whether the handler is async (default: False)
        """
        if is_async:
            self._wildcard_async_handlers.append(handler)
        else:
            self._wildcard_sync_handlers.append(handler)

        logger.info(f"Subscribed {'async' if is_async else 'sync'} wildcard handler")

    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
        is_async: bool = False
    ) -> None:
        """Unsubscribe from events of a specific type.

        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler function to remove
            is_async: Whether the handler is async (default: False)
        """
        handlers = self._async_handlers if is_async else self._sync_handlers

        if event_type in handlers and handler in handlers[event_type]:
            handlers[event_type].remove(handler)
            logger.info(f"Unsubscribed handler from {event_type}")

    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all subscribers.

        This is a synchronous method that calls all handlers.
        For async handlers, use publish_async().

        Args:
            event: The event to publish
        """
        event_type = event.event_type

        # Add to history
        self._add_to_history(event)

        # Call event-specific handlers
        handlers = self._sync_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}", exc_info=True)

        # Call wildcard handlers
        for handler in self._wildcard_sync_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in wildcard event handler: {e}", exc_info=True)

        logger.debug(f"Published event {event.event_type} (id: {event.event_id})")

    async def publish_async(self, event: BaseEvent) -> None:
        """Publish an event to all subscribers (async).

        This method calls both sync and async handlers.
        Sync handlers are called in the current thread.
        Async handlers are awaited.

        Args:
            event: The event to publish
        """
        event_type = event.event_type

        # Add to history
        self._add_to_history(event)

        # Call sync handlers (in current thread)
        self.publish(event)

        # Call async handlers
        async_handlers = self._async_handlers.get(event_type, [])
        for handler in async_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in async event handler for {event_type}: {e}", exc_info=True)

        # Call async wildcard handlers
        for handler in self._wildcard_async_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in async wildcard event handler: {e}", exc_info=True)

        logger.debug(f"Published async event {event.event_type} (id: {event.event_id})")

    def _add_to_history(self, event: BaseEvent) -> None:
        """Add event to history for debugging.

        Args:
            event: The event to add
        """
        self._published_events.append(event)

        # Keep history size limited
        if len(self._published_events) > self._max_history:
            self._published_events = self._published_events[-self._max_history:]

    def get_history(
        self,
        event_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        limit: int = 100
    ) -> List[BaseEvent]:
        """Get event history for debugging.

        Args:
            event_type: Filter by event type
            aggregate_id: Filter by aggregate ID
            limit: Maximum number of events to return

        Returns:
            List of published events (most recent first)
        """
        events = self._published_events[::-1]  # Reverse for most recent first

        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if aggregate_id:
            events = [e for e in events if e.aggregate_id == aggregate_id]

        return events[:limit]

    def clear_history(self) -> None:
        """Clear event history."""
        self._published_events.clear()
        logger.info("Cleared event bus history")

    def get_subscriber_count(self, event_type: Optional[str] = None) -> int:
        """Get the number of subscribers for an event type.

        Args:
            event_type: The event type, or None for wildcard subscribers

        Returns:
            Number of subscribers
        """
        if event_type is None:
            return len(self._wildcard_sync_handlers) + len(self._wildcard_async_handlers)

        sync_count = len(self._sync_handlers.get(event_type, []))
        async_count = len(self._async_handlers.get(event_type, []))

        return sync_count + async_count


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance.

    Returns:
        The global event bus
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (useful for testing)."""
    global _event_bus
    _event_bus = None


# Type hints
from typing import Optional
