from application.abstract.events import BaseEventHandler
from core.messages.finance import GetFinanceMessages
from domain.finance.exceptions import AccountTransactionStartBonusExist
from application.events.handler_groups import HandlerGroups
from application.finance.dtos.account_transaction import CreateAccountTransactionDTO
from application.finance.events import TransactionStartBonusEvent, TransactionErrorEvent
from application.finance.services.account_transaction_service import AccountTransactionService
from application.finance.utils.transaction_factory import create_transaction_from_dto
from domain.finance.enums.transaction_type import TransactionType
from core.config import settings


class TransactionStartBonusEventHandler(BaseEventHandler[TransactionStartBonusEvent, TransactionErrorEvent]):
    """
    Handles init start bonus
    """
    event_type = TransactionStartBonusEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    @BaseEventHandler.with_streaming
    @BaseEventHandler.with_error(TransactionErrorEvent, expected_errors=[AccountTransactionStartBonusExist])
    async def handler(cls, event: TransactionStartBonusEvent) -> None:
        transaction_service = AccountTransactionService()
        has_start_bonus = len(await transaction_service.repository.list_by_account_and_transaction_type(
            account_id=event.account_id, transaction_type=TransactionType.START_BONUS)) > 0
        if has_start_bonus:
            raise AccountTransactionStartBonusExist(GetFinanceMessages.start_bonus_exist())
        await create_transaction_from_dto(
            CreateAccountTransactionDTO(
                account_id=event.account_id,
                transaction_type=TransactionType.START_BONUS,
                credits_amount=settings.credits_start_bonus
            ),
            pid=event.pid
        )
