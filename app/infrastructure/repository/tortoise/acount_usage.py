from domain.finance.entities import AccountUsageEntity
from domain.finance.interfaces import AccountUsageRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models.finance import AccountUsageModel


class TortoiseAccountUsageRepository(BaseTortoiseRepository[AccountUsageEntity, AccountUsageModel],
                                     AccountUsageRepository):
    model = AccountUsageModel

    async def to_entity(self, o: AccountUsageModel) -> AccountUsageEntity:
        return AccountUsageEntity(
            id=o.id,
            account_id=o.account_id,
            credits_amount=o.credits_amount,
            usage_id=o.usage_id,
            usage_type=o.usage_type,
            usage_amount=o.usage_amount,
            canceled_at=o.canceled_at,
            created_at=o.created_at,
            updated_at=o.updated_at
        )

    @BaseTortoiseRepository.read()
    async def list_by_account(self, account_id: int) -> list[AccountUsageEntity]:
        models = await AccountUsageModel.filter(account_id=account_id).all()
        return [await self.to_entity(model) for model in models]
