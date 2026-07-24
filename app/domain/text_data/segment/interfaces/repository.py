from __future__ import annotations
from abc import abstractmethod

from domain.abstract import EntityRepository
from domain.text_data.segment.entities import SegmentTranslateEntity, SegmentVoiceEntity, \
    WordTranslateSegmentTranslateEntity


class SegmentTranslateRepository(EntityRepository[SegmentTranslateEntity]):
    """
    Repository interface for segment translation records.
    """

    @abstractmethod
    async def get_by_segment(self, segment_id: int, language_id: int, account_id: int) -> SegmentTranslateEntity | None:
        """
        Retrieve translation for a specific segment, language, and account.
        """
        ...


class SegmentVoiceRepository(EntityRepository[SegmentVoiceEntity]):
    """
    Repository interface for segment voice records.
    """

    @abstractmethod
    async def get_by_segment(self, segment_id: int) -> SegmentVoiceEntity | None:
        """
        Retrieve the voice record for a given segment.
        """
        ...


class WordTranslateSegmentTranslateRepository(EntityRepository[WordTranslateSegmentTranslateEntity]):
    """
    Repository interface for the linking table between word translations and segment translations.
    """

    @abstractmethod
    async def get_by_segment(self, segment_id: int) -> list[WordTranslateSegmentTranslateEntity]:
        """
        Get all word-translation links related to a specific segment translation.
        """
        ...
