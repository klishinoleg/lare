from __future__ import annotations
from domain.text.segment.entities import SegmentEntity
from domain.text.segment.interfaces.repository import SegmentRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models import SegmentModel


class TortoiseSegmentRepository(
    BaseTortoiseRepository[SegmentEntity, SegmentModel], SegmentRepository
):
    model = SegmentModel

    @staticmethod
    async def to_entity(o: SegmentModel) -> SegmentEntity:
        return SegmentEntity(
            id=o.id,
            name=o.name,
            language_id=o.language_id
        )

    @BaseTortoiseRepository.read()
    async def get_by_name_and_language(self, name: str, language_id: int) -> SegmentEntity | None:
        obj = await self.model.filter(name=name, language_id=language_id).first()
        return await self.to_entity(obj) if obj else None
