from domain.ai.entities import AiLogEntity
from domain.ai.interfaces.repository import AiLogRepository
from domain.finance.enums.account_usage_type import AccountUsageType
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models.ai_log import AiLogModel


class TortoiseAiLogRepository(
    BaseTortoiseRepository[AiLogEntity, AiLogModel],
    AiLogRepository
):
    model = AiLogModel

    @staticmethod
    async def to_entity(o: AiLogModel) -> AiLogEntity:
        return AiLogEntity(
            id=o.id,
            ai_request=o.ai_request,
            ai_response=o.ai_response,
            ai_type=o.ai_type,
            ai_model_id=o.ai_model_id,
            file_path=o.file_path,
            source_language=o.source_language_id,
            target_language=o.target_language_id,
            usage_type=o.usage_type,
            account_id=o.account_id,
            hash_str=o.hash_str,
        )

    @BaseTortoiseRepository.read()
    async def get_by_hash(
        self,
        hash_str: str,
        usage_type: AccountUsageType,
        ai_type: str,
    ) -> AiLogEntity | None:
        obj = await self.model.filter(
            hash_str=hash_str,
            usage_type=usage_type,
            ai_type=ai_type
        ).first()
        return await self.to_entity(obj) if obj else None

    async def save(self, entity: AiLogEntity) -> AiLogEntity | None:
        data = entity.to_dict(exclude_id=True)
        data.pop("created_at", None)
        data.pop("updated_at", None)
        data["source_language_id"] = data.pop("source_language")
        data["target_language_id"] = data.pop("target_language")

        if entity.id is None:
            obj = await self.model.create(**data)
        else:
            obj = await self.model.get_or_none(id=entity.id)
            if obj is None:
                return None
            obj.update_from_dict(data)
            await obj.save()
        return await self.to_entity(obj)


TortoiseAiRequestLogRepository = TortoiseAiLogRepository
