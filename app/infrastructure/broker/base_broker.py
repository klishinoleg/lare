import asyncio
from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Type

from application.abstract.events import BaseEventHandler, BaseEvent


class BaseBroker(ABC):
    """
    Abstract base class for event subscribers.
    """

    def __init__(self) -> None:
        self.before_start_handlers: list[Callable[[], Awaitable]] = []

    def run(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        for func in self.before_start_handlers:
            await func()
        await self._start_broker()

    @abstractmethod
    async def _start_broker(self) -> None:
        ...

    @abstractmethod
    def subscribe[BEH: BaseEventHandler, BE: BaseEvent](self, handler: Type[BEH], event_model: Type[BE]) -> None:
        """
        Subscribe to all events and call the provided handler.
        """
        raise NotImplementedError

    def before_start(self, func: Callable[[], Awaitable]) -> None:
        self.before_start_handlers.append(func)
