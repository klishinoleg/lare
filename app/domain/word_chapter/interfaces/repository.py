from __future__ import annotations
from abc import abstractmethod
from domain.abstract import EntityRepository
from domain.word_chapter.entities import WordChapter


class WordChapterRepository(EntityRepository[WordChapter]):
    """
    Abstract repository interface for Word-in-chapter entities.
    """

    @abstractmethod
    async def get_by_chapter(self, chapter_id: int) -> list[WordChapter]:
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
