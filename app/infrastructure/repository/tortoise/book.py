from __future__ import annotations
from domain.book.interfaces.repository import BookRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models import BookModel
from domain.book.entities import BookEntity


class TortoiseBookRepository(BaseTortoiseRepository[BookEntity, BookModel], BookRepository):
    model = BookModel

    @staticmethod
    async def to_entity(o: BookModel) -> BookEntity:
        return BookEntity(
            id=o.id,
            name=o.name,
            image=await getattr(o, "croped_image"),
            account_id=getattr(o, "account_id"),
            language_id=getattr(o, "language_id"),
            chapters_cnt=o.chapters_count,
            updated_at=o.updated_at,
            created_at=o.created_at
        )

    @BaseTortoiseRepository.read()
    async def get_by_account(self, account_id: int) -> list[BookEntity]:
        return [await self.to_entity(o) for o in await self.model.filter(account_id=account_id).all()]
