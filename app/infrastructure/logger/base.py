from abc import ABC, abstractmethod
from application.abstract.events import BaseEvent


class BaseLogger(ABC):
    @abstractmethod
    async def event_log(self, event: BaseEvent) -> None:
        """
        Log event.
        """
        pass
