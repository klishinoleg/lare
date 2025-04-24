from application.account.services import AccountService
from application.finance.dtos.account_transaction import AccountTransactionDTO, AccountTransactionListDTO, \
    CreateAccountTransactionDTO, UpdateAccountTransactionDTO
from application.finance.events import TransactionCreatedEvent, TransactionErrorEvent
from core.di.events import DIPublisher
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
        try:
            account_transaction_entity: AccountTransactionEntity = await super().create(entity)
            await self._recalculate_account_credits(account_transaction_entity.account_id)
            await DIPublisher[TransactionCreatedEvent].publish(
                payload=TransactionCreatedEvent(
                    account_id=account_transaction_entity.account_id,
                    usage_id=account_transaction_entity.usage_id,
                    transaction_type=account_transaction_entity.transaction_type,
                    credits_amount=account_transaction_entity.credits_amount
                ),
                group_id=f"account:{account_transaction_entity.account_id}"
            )
            return entity
        except Exception as ex:
            await DIPublisher[TransactionErrorEvent].publish_error(
                event_error_model=TransactionErrorEvent,
                ex=ex,
                step=TransactionCreatedEvent.event_type,
                group_id=f"account:{entity.account_id}",
                account_id=entity.account_id,
            )
            raise
