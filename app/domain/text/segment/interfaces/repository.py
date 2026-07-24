from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from domain.abstract import EntityRepository
from domain.text.segment.entities import SegmentEntity


class SegmentRepository(EntityRepository[SegmentEntity], ABC):
    """
    Repository interface for accessing and managing segments.
    """

    @abstractmethod
    async def get_by_name_and_language(self, name: str, language_id: int) -> SegmentEntity | None:
        """
        Retrieve a segment by its exact text and source language.
        """
        ...
