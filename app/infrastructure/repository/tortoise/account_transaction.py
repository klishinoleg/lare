from domain.finance.entities import AccountTransactionEntity
from domain.finance.interfaces import AccountTransactionRepository
from domain.finance.enums.transaction_type import TransactionType
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models.finance import AccountTransactionModel


class TortoiseAccountTransactionRepository(BaseTortoiseRepository[AccountTransactionEntity, AccountTransactionModel],
                                           AccountTransactionRepository):
    model = AccountTransactionModel

    async def to_entity(self, o: AccountTransactionModel) -> AccountTransactionEntity:
        return AccountTransactionEntity(
            account_id=o.account_id,
            transaction_type=o.transaction_type,
            credits_amount=o.credits_amount,
            usage_id=o.usage_id,
            bill_id=o.bill_id,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )

    @BaseTortoiseRepository.read()
    async def list_by_account(self, account_id: int) -> list[AccountTransactionEntity]:
        models = await AccountTransactionModel.filter(account_id=account_id).all()
        return [await self.to_entity(model) for model in models]

    @BaseTortoiseRepository.read()
    async def list_by_account_and_transaction_type(
            self, account_id: int, transaction_type: TransactionType) -> list[AccountTransactionEntity]:
        models = await AccountTransactionModel.filter(account_id=account_id, transaction_type=transaction_type).all()
        return [await self.to_entity(model) for model in models]

    @BaseTortoiseRepository.read()
    async def check_usage_exist(self, usage_id: int) -> bool:
        return await AccountTransactionModel.filter(usage_id=usage_id).exists()

    @BaseTortoiseRepository.read()
    async def check_bill_and_transaction_type_exist(self, bill_id: int, transaction_type: TransactionType) -> bool:
        return await AccountTransactionModel.filter(bill_id=bill_id, transaction_type=transaction_type).exists()
