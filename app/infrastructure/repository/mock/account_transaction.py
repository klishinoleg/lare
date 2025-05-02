from domain.finance.entities import AccountTransactionEntity
from domain.finance.interfaces import AccountTransactionRepository
from domain.finance.enums.transaction_type import TransactionType
from infrastructure.repository.mock.base_repository import BaseMockRepository


class MockAccountTransactionRepository(BaseMockRepository[AccountTransactionEntity], AccountTransactionRepository):
    async def list_by_account(self, account_id: int) -> list[AccountTransactionEntity]:
        return [t for t in self.entities.values() if t.account_id == account_id]

    async def list_by_account_and_transaction_type(
            self, account_id: int, transaction_type: TransactionType
    ) -> list[AccountTransactionEntity]:
        return [
            t for t in self.entities.values()
            if t.account_id == account_id and t.transaction_type == transaction_type
        ]

    async def check_usage_exist(self, usage_id: int) -> bool:
        return any(t.usage_id == usage_id for t in self.entities.values())

    async def check_bill_and_transaction_type_exist(self, bill_id: int, transaction_type: TransactionType) -> bool:
        return any(
            t.bill_id == bill_id and t.transaction_type == transaction_type
            for t in self.entities.values()
        )
