from __future__ import annotations

from domain.book.entities import ChapterEntity
from domain.book.interfaces.repository import ChapterRepository
from infrastructure.repository.mock.base_repository import BaseMockRepository


class MockChapterRepository(BaseMockRepository[ChapterEntity], ChapterRepository):
    """
    In-memory mock implementation of ChapterRepository.
    """

    async def get_by_book(self, book_id: int, account_id: int) -> list[ChapterEntity]:
        return [
            chapter for chapter in self.entities.values()
            if chapter.book_id == book_id
        ]
