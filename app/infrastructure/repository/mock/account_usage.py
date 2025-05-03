from domain.finance.entities import AccountUsageEntity
from domain.finance.interfaces import AccountUsageRepository
from infrastructure.repository.mock.base_repository import BaseMockRepository


class MockAccountUsageRepository(BaseMockRepository[AccountUsageEntity], AccountUsageRepository):
    async def list_by_account(self, account_id: int) -> list[AccountUsageEntity]:
        return [u for u in self.entities.values() if u.account_id == account_id]
