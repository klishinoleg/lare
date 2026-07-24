from domain.ai.entities import AiModelEntity
from domain.ai.interfaces.repository import AiModelRepository
from domain.finance.enums.account_usage_type import AccountUsageType
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models import AiModelModel


class TortoiseAiModelRepository(
    BaseTortoiseRepository[AiModelEntity, AiModelModel],
    AiModelRepository
):
    model = AiModelModel

    @staticmethod
    async def to_entity(o: AiModelModel) -> AiModelEntity:
        return AiModelEntity(
            id=o.id,
            name=o.name,
            model=o.model,
            input_cost=o.input_cost,
            output_cost=o.output_cost,
            kef=o.kef,
            allow_to=[AccountUsageType(item) for item in o.allow_to],
            is_active=o.is_active
        )

    @BaseTortoiseRepository.read()
    async def get_by_model(self, model: str) -> AiModelEntity | None:
        obj = await self.model.filter(model=model).first()
        return await self.to_entity(obj) if obj else None

    @BaseTortoiseRepository.read()
    async def get_available_for_usage(self, usage_type: AccountUsageType) -> list[AiModelEntity]:
        objs = await self.model.filter(
            is_active=True,
            allow_to__contains=[usage_type.value]
        ).all()
        return [await self.to_entity(obj) for obj in objs]

    async def save(self, entity: AiModelEntity) -> AiModelEntity | None:
        data = entity.to_dict(exclude_id=True)
        data["allow_to"] = [
            item.value if isinstance(item, AccountUsageType) else item
            for item in entity.allow_to
        ]
        if entity.id is None:
            obj = await self.model.create(**data)
        else:
            obj = await self.model.get_or_none(id=entity.id)
            if obj is None:
                return None
            obj.update_from_dict(data)
            await obj.save()
        return await self.to_entity(obj)
