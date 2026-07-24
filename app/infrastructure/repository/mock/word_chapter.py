from __future__ import annotations

from domain.text.word_chapter.interfaces.repository import WordChapterRepository
from domain.text.word_chapter.entities import WordChapterEntity
from infrastructure.repository.mock.base_repository import BaseMockRepository


class MockWordChapterRepository(BaseMockRepository[WordChapterEntity], WordChapterRepository):
    """
    In-memory mock implementation of WordChapterRepository for testing.
    """

    async def get_by_chapter(self, chapter_id: int) -> list[WordChapterEntity]:
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
