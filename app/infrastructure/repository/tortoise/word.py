from __future__ import annotations

from domain.word.interfaces.repository import WordRepository
from domain.word.entities import WordEntity
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models import WordModel


class TortoiseWordRepository(BaseTortoiseRepository[WordEntity, WordModel], WordRepository):
    model = WordModel

    @staticmethod
    async def to_entity(o: WordModel) -> WordEntity:
        return WordEntity(
            id=o.id,
            name=o.name,
            language_id=getattr(o, "language_id"),
        )

    async def get_by_name_and_language(self, name: str, language_id: int) -> WordEntity | None:
        instance = await self.model.filter(name=name, language_id=language_id).first()
        if instance:
            return await self.to_entity(instance)
        return None

    async def get_many_by_ids(self, ids: list[int]) -> list[WordEntity]:
        return [await self.to_entity(o) for o in await self.model.filter(id__in=ids).all()]
