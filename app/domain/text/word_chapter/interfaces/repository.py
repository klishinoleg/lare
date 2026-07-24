from __future__ import annotations
from abc import abstractmethod
from domain.abstract import EntityRepository
from domain.text.word_chapter.entities import WordChapterEntity


class WordChapterRepository(EntityRepository[WordChapterEntity]):
    """
    Abstract repository interface for Word-in-chapter entities.
    """

    @abstractmethod
    async def get_by_chapter(self, chapter_id: int) -> list[WordChapterEntity]:
        """
        Retrieve all words linked to a specific chapter.
        """
        ...

    @abstractmethod
    async def delete_by_chapter(self, chapter_id: int) -> None:
        """
        Delete all word entries for a specific chapter.
        """
        ...
