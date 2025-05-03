from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent


class BasePublisher[BE: "BaseEvent"](ABC):

    @classmethod
    @abstractmethod
    async def publish(cls, payload: BE, group_id: str | None) -> None:
        ...

    @classmethod
    async def on_start(cls) -> None:
        ...

    @classmethod
    async def on_stop(cls) -> None:
        ...
