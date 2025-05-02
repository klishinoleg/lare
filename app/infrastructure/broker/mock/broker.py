from collections import defaultdict
from typing import Type, Callable, Awaitable, TYPE_CHECKING
from application.events.event_types import EventTypes
from infrastructure.broker.base_broker import BaseBroker

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent, BaseEventHandler


class MockEventBroker[BEH: "BaseEventHandler", BE: "BaseEvent"](BaseBroker):
    """
    Mock implementation of event subscriber.
    """

    subscribers: dict[EventTypes, dict[str, Type[BEH]]] = defaultdict(dict)

    def subscribe(self, handler: Type[BEH], event_model: Type[BE]) -> None:
        self.subscribers[event_model.event_type][handler.event_handler_group] = handler

    async def _start_broker(self) -> None:
        ...

    def before_start(self, func: Callable[[], Awaitable]) -> None:
        ...
