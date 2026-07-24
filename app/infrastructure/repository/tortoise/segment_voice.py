from domain.text_data.segment.entities import SegmentVoiceEntity
from domain.text_data.segment.interfaces.repository import SegmentVoiceRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models import SegmentVoiceModel


class TortoiseSegmentVoiceRepository(
    BaseTortoiseRepository[SegmentVoiceEntity, SegmentVoiceModel],
    SegmentVoiceRepository
):
    model = SegmentVoiceModel

    @staticmethod
    async def to_entity(o: SegmentVoiceModel) -> SegmentVoiceEntity:
        return SegmentVoiceEntity(
            id=o.id,
            segment_id=o.segment_id,
            file_path=o.file_path,
        )

    @BaseTortoiseRepository.read()
    async def get_by_segment(self, segment_id: int) -> SegmentVoiceEntity | None:
        obj = await self.model.filter(segment_id=segment_id).first()
        return await self.to_entity(obj) if obj else None
