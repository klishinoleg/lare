from abc import ABC, abstractmethod
from uuid import UUID


class BaseEventDeduplicatorService(ABC):
    @abstractmethod
    async def is_duplicate(self, event_id: UUID) -> bool:
        """
        Check whether event ID has already been processed.
        """
        raise NotImplementedError
