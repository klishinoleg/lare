from abc import ABC, abstractmethod
from application.abstract.events import BaseErrorEvent


class BaseLogger[BE: BaseErrorEvent](ABC):

    async def event_log(self, event: BE) -> None:
        if event.is_expected:
            return
        await self._event_log(event)

    @abstractmethod
    async def _event_log(self, event: BE) -> None:
        """
        Log event.
        """
        pass
