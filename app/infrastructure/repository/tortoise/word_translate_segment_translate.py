from domain.text_data.segment.entities import WordTranslateSegmentTranslateEntity
from domain.text_data.segment.interfaces.repository import WordTranslateSegmentTranslateRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models import WordTranslateSegmentTranslateModel


class TortoiseWordTranslateSegmentTranslateRepository(
    BaseTortoiseRepository[
        WordTranslateSegmentTranslateEntity,
        WordTranslateSegmentTranslateModel
    ],
    WordTranslateSegmentTranslateRepository,
):
    model = WordTranslateSegmentTranslateModel

    @staticmethod
    async def to_entity(o: WordTranslateSegmentTranslateModel) -> WordTranslateSegmentTranslateEntity:
        return WordTranslateSegmentTranslateEntity(
            id=o.id,
            segment_id=o.segment_translate_id,
            word_translate_id=o.word_translate_id,
        )

    @BaseTortoiseRepository.read()
    async def get_by_segment(self, segment_id: int) -> list[WordTranslateSegmentTranslateEntity]:
        objects = await self.model.filter(segment_translate_id=segment_id).all()
        return [await self.to_entity(o) for o in objects]
