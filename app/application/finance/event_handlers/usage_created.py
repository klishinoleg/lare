from decimal import Decimal

from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.finance.dtos.account_transaction import CreateAccountTransactionDTO
from application.finance.events import UsageCreatedEvent
from application.finance.services.account_transaction_service import AccountTransactionService
from domain.finance.entities import AccountTransactionEntity
from domain.finance.enums.transaction_type import TransactionType


class UsageCreatedEventHandler(BaseEventHandler[UsageCreatedEvent]):
    """
    Handles UsageCreatedEvent: creates a corresponding transaction.
    """
    event_type = UsageCreatedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    async def handler(cls, event: UsageCreatedEvent, group_id: int | None) -> None:
        transaction_service = AccountTransactionService()
        create_transaction_dto = CreateAccountTransactionDTO(
            account_id=event.account_id,
            transaction_type=TransactionType.AI_USAGE,
            credits_amount=event.credits_amount * Decimal(-1),
            usage_id=event.usage_id
        )
        transaction_entity = AccountTransactionEntity(**create_transaction_dto.model_dump())
        await transaction_service.create(transaction_entity)
