from typing import TypeVar, Callable, Awaitable, Dict, Type
from application.events.event_types import EventTypes
from application.abstract.events import BaseEvent

E = TypeVar("E", bound=BaseEvent)

EventHandler = Callable[[E], Awaitable[None]]

event_handlers: Dict[EventTypes, tuple[Type[BaseEvent], EventHandler]] = {}


def register_event_handler(event_type: EventTypes, event_model: Type[BaseEvent]) -> Callable:
    """
    Decorator to register an event handler for a given event type and event model.

    Args:
        event_type (EventTypes): Event type to listen for.
        event_model (Type[BaseEvent]): Pydantic model of the event payload.
    """

    def decorator(func: EventHandler) -> EventHandler:
        event_handlers[event_type] = (event_model, func)
        return func

    return decorator
