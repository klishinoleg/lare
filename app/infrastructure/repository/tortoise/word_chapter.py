from __future__ import annotations

from domain.text.word_chapter.interfaces.repository import WordChapterRepository
from domain.text.word_chapter.entities import WordChapterEntity
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models import WordChapterModel


class TortoiseWordChapterRepository(BaseTortoiseRepository[WordChapterEntity, WordChapterModel], WordChapterRepository):
    model = WordChapterModel

    @staticmethod
    async def to_entity(o: WordChapterModel) -> WordChapterEntity:
        return WordChapterEntity(
            id=o.id,
            name=o.name,
            word_id=o.word_id,
            chapter_id=o.chapter_id,
            position=o.position,
            n=o.n,
            phrase_id=o.phrase_id,
            segment_id=o.segment_id
        )

    @BaseTortoiseRepository.read()
    async def get_by_chapter(self, chapter_id: int) -> list[WordChapterEntity]:
        return [await self.to_entity(o) for o in await self.model.filter(chapter_id=chapter_id).all()]

    @BaseTortoiseRepository.write()
    async def delete_by_chapter(self, chapter_id: int) -> None:
        await self.model.filter(chapter_id=chapter_id).delete()
