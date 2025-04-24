from __future__ import annotations
from domain.book.entities import ChapterEntity
from domain.book.interfaces.repository import ChapterRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models.chapter import ChapterModel


class TortoiseChapterRepository(BaseTortoiseRepository[ChapterModel, ChapterEntity], ChapterRepository):
    """
    Tortoise ORM implementation of ChapterRepository.
    """
    model = ChapterModel

    async def to_entity(self, model: ChapterModel) -> ChapterEntity:
        return ChapterEntity(
            id=model.id,
            name=model.name,
            book_id=model.book_id,
            account_id=model.account_id,
            source_url=model.source_url,
            position=model.position,
            is_ready=model.is_ready,
        )

    async def get_by_book(self, book_id: int, account_id: int) -> list[ChapterEntity]:
        models = await ChapterModel.filter(book_id=book_id, book__account_id=account_id).all()
        return [await self.to_entity(model) for model in models]
