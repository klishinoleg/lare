from abc import ABC, abstractmethod
from application.abstract.events import BaseErrorEvent


class BaseLogger(ABC):
    @abstractmethod
    async def event_log(self, event: BaseErrorEvent) -> None:
        """
        Log event.
        """
        pass
