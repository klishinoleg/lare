from abc import ABC, abstractmethod


class BaseEventDeduplicatorService(ABC):
    @abstractmethod
    async def is_duplicate(self, event_id: str) -> bool:
        """
        Check whether event ID has already been processed.
        """
        raise NotImplementedError
