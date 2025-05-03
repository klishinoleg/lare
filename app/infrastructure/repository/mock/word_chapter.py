from __future__ import annotations

from domain.word_chapter.interfaces.repository import WordChapterRepository
from domain.word_chapter.entities import WordChapter
from infrastructure.repository.mock.base_repository import BaseMockRepository


class MockWordChapterRepository(BaseMockRepository[WordChapter], WordChapterRepository):
    """
    In-memory mock implementation of WordChapterRepository for testing.
    """

    async def get_by_chapter(self, chapter_id: int) -> list[WordChapter]:
        """
        Retrieve all word chapters linked to a specific chapter.
        """
        return [wc for wc in self.entities.values() if wc.chapter_id == chapter_id]

    async def delete_by_chapter(self, chapter_id: int) -> None:
        """
        Delete all word chapters linked to a specific chapter.
        """
        to_delete = [wc_id for wc_id, wc in self.entities.items() if wc.chapter_id == chapter_id]
        for wc_id in to_delete:
            self.entities.pop(wc_id, None)
