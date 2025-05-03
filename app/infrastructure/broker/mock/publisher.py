from typing import TYPE_CHECKING

from application.events.event_types import EventTypes
from infrastructure.broker.base_publisher import BasePublisher
from infrastructure.broker.mock.broker import MockEventBroker

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent


class MockPublisher[BE: "BaseEvent"](BasePublisher):
    _events: list[tuple[EventTypes, BE]] = []

    @classmethod
    async def publish(cls, payload: BE, group_id: str | None) -> None:
        if payload.event_type in MockEventBroker.subscribers:
            cls._events.append((payload.event_type, payload))
            for group, Handler in MockEventBroker.subscribers[payload.event_type].items():
                await Handler.handler(payload)

    @classmethod
    def get_events(cls) -> list[tuple[EventTypes, BE]]:
        return cls._events

    @classmethod
    def clear_events(cls) -> None:
        cls._events.clear()
