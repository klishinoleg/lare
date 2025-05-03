from application.account.services import AccountService
from application.finance.dtos.account_transaction import AccountTransactionDTO, AccountTransactionListDTO, \
    CreateAccountTransactionDTO, UpdateAccountTransactionDTO
from domain.finance.entities import AccountTransactionEntity
from application.abstract.services.crud import BaseCRUDService
from core.enums.repository.types import RepositoryTypes
from domain.finance.interfaces import AccountTransactionRepository


class AccountTransactionService(
    BaseCRUDService[
        AccountTransactionEntity,
        AccountTransactionRepository,
        AccountTransactionDTO,
        AccountTransactionListDTO,
        CreateAccountTransactionDTO,
        UpdateAccountTransactionDTO
    ]
):
    entity_class = AccountTransactionEntity
    entity_repository_type = AccountTransactionRepository
    repository_type = RepositoryTypes.TORTOISE

    async def _delete_modificate__recalculate_credits(self,
                                                      entity: AccountTransactionEntity) -> AccountTransactionEntity:
        await self._recalculate_account_credits(entity.account_id)
        return entity

    async def _recalculate_account_credits(self, account_id: int) -> None:
        transactions = await self.repository.list_by_account(account_id)
        total_credits = sum(t.credits_amount for t in transactions)
        await AccountService(self.repository_type).repository.update_credits(account_id, total_credits)

    async def create(self, entity: AccountTransactionEntity) -> AccountTransactionEntity:
        account_transaction_entity: AccountTransactionEntity = await super().create(entity)
        await self._recalculate_account_credits(account_transaction_entity.account_id)
        return entity
