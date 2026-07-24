from domain.text_data.segment.entities import SegmentTranslateEntity
from domain.text_data.segment.interfaces.repository import SegmentTranslateRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models import SegmentTranslateModel


class TortoiseSegmentTranslateRepository(
    BaseTortoiseRepository[SegmentTranslateEntity, SegmentTranslateModel],
    SegmentTranslateRepository
):
    model = SegmentTranslateModel

    @staticmethod
    async def to_entity(o: SegmentTranslateModel) -> SegmentTranslateEntity:
        return SegmentTranslateEntity(
            id=o.id,
            segment_id=o.segment_id,
            language_id=o.language_id,
            account_id=o.account_id,
            translate=o.translate,
        )

    @BaseTortoiseRepository.read()
    async def get_by_segment(self, segment_id: int, language_id: int, account_id: int) -> SegmentTranslateEntity | None:
        obj = await self.model.filter(
            segment_id=segment_id,
            language_id=language_id,
            account_id=account_id
        ).first()
        return await self.to_entity(obj) if obj else None
