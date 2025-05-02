from decimal import Decimal

from application.events.streaming.types import StreamingTypes
from application.finance.dtos.account_transaction import CreateAccountTransactionDTO
from application.finance.services.account_transaction_service import AccountTransactionService
from application.finance.events import TransactionCreatedEvent, UsageCreatedEvent, UsageCancelledEvent, \
    TransactionStartBonusEvent, TransactionErrorEvent
from core.di.events import DIPublisher, DIEventStreaming
from domain.finance.entities import AccountTransactionEntity, BillEntity
from domain.finance.enums.transaction_type import TransactionType
from infrastructure.event_streaming.base import BaseEventStreaming


async def create_transaction_from_dto(dto: CreateAccountTransactionDTO,
                                      pid: None | str = None) -> AccountTransactionEntity:
    """
    Creates a transaction entity from a DTO and publishes a TransactionCreatedEvent.
    """
    entity = AccountTransactionEntity(**dto.model_dump())
    saved = await AccountTransactionService().create(entity)
    await DIPublisher[TransactionCreatedEvent, TransactionErrorEvent].publish(
        payload=TransactionCreatedEvent(
            account_id=saved.account_id,
            usage_id=saved.usage_id,
            transaction_type=saved.transaction_type,
            credits_amount=saved.credits_amount,
            bill_id=dto.bill_id,
            pid=pid
        ),
        group_id=f"account:{saved.account_id}"
    )
    return saved


async def publish_start_bonus_transaction(account_id: int, pid: str | None = None) -> None:
    await DIPublisher.publish(TransactionStartBonusEvent(account_id=account_id, pid=pid))


async def publish_start_bonus_transaction_with_streaming(account_id: int) -> BaseEventStreaming:
    event_streaming = DIEventStreaming.get(*(account_id,), streaming_type=StreamingTypes.START_BONUS)
    await publish_start_bonus_transaction(account_id=account_id, pid=event_streaming.get_pid())
    return event_streaming


def make_transaction_dto_from_usage_event(
        usage_event: UsageCreatedEvent | UsageCancelledEvent
) -> CreateAccountTransactionDTO:
    """
    Maps usage event data to a CreateAccountTransactionDTO.
    """
    is_cancel = isinstance(usage_event, UsageCancelledEvent)
    return CreateAccountTransactionDTO(
        account_id=usage_event.account_id,
        usage_id=usage_event.usage_id,
        credits_amount=usage_event.credits_amount * Decimal(1 if is_cancel else -1),
        transaction_type=TransactionType.AI_USAGE_CANCEL if is_cancel else TransactionType.AI_USAGE
    )


def make_transaction_dto_from_bill(
        bill: BillEntity, refund: bool = False
) -> CreateAccountTransactionDTO:
    """
    Maps bill to a CreateAccountTransactionDTO.
    """
    return CreateAccountTransactionDTO(
        account_id=bill.account_id,
        bill_id=bill.id,
        credits_amount=bill.credits_amount * Decimal(-1 if refund else 1),
        transaction_type=TransactionType.REFUND if refund else TransactionType.PAYMENT
    )
