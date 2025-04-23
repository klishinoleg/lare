from abc import ABC, abstractmethod
from application.abstract.events import BaseEvent


class BasePublisher(ABC):

    @classmethod
    @abstractmethod
    async def publish(cls, payload: BaseEvent, group_id: str | None) -> None:
        ...
