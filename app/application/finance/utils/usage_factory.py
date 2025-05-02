from datetime import datetime, timezone
from application.finance.dtos.acount_usage import CreateAccountUsageDTO
from application.finance.events import UsageCreatedEvent, UsageErrorEvent, UsageCancelledEvent
from application.finance.services.account_usage_service import AccountUsageService
from core.di.events import DIPublisher
from domain.finance.entities import AccountUsageEntity


async def create_usage_event(create_account_usage_dto: CreateAccountUsageDTO, pid: str | None = None) -> AccountUsageEntity:
    """
    Create a new usage record and publish UsageCreatedEvent.

    Args:
        entity (CreateAccountUsageDTO): Usage data to be saved.

    Returns:
        :param pid:
        :param create_account_usage_dto:
    """
    usage_id = None
    try:
        account_usage = AccountUsageEntity(**create_account_usage_dto.model_dump())
        account_usage_saved = await AccountUsageService().create(account_usage)
        usage_id = account_usage_saved.id
        await DIPublisher[UsageCreatedEvent, UsageErrorEvent].publish(
            payload=UsageCreatedEvent(
                usage_type=account_usage_saved.usage_type,
                usage_id=account_usage_saved.id,
                account_id=account_usage_saved.account_id,
                credits_amount=account_usage_saved.credits_amount,
                pid=pid
            ),
            group_id=f"account:{account_usage_saved.account_id}"
        )
        return account_usage_saved
    except Exception as ex:
        await DIPublisher[UsageErrorEvent, UsageErrorEvent].publish_error(
            event_error_model=UsageErrorEvent,
            ex=ex,
            step=UsageCreatedEvent.event_type,
            group_id=f"account:{create_account_usage_dto.account_id}",
            account_id=create_account_usage_dto.account_id,
            usage_id=usage_id,
            usage_type=create_account_usage_dto.usage_type,
            credits_amount=create_account_usage_dto.credits_amount,
            pid=pid
        )
        raise


async def cancel_usage_event(account_usage_entity: AccountUsageEntity, pid: str | None = None) -> None:
    """
    Cancel an existing usage entry and trigger UsageCancelledEvent.

    Args:
        :param pid:
        :param account_usage_entity:
    """
    try:
        account_usage_entity.canceled_at = datetime.now(tz=timezone.utc)
        await AccountUsageService().update(account_usage_entity, is_system=True)
        await DIPublisher[UsageCancelledEvent, UsageErrorEvent].publish(
            payload=UsageCancelledEvent(
                account_id=account_usage_entity.account_id,
                usage_type=account_usage_entity.usage_type,
                usage_id=account_usage_entity.id,
                credits_amount=account_usage_entity.credits_amount,
                pid=pid
            ),
            group_id=f"account:{account_usage_entity.account_id}"
        )
    except Exception as ex:
        await DIPublisher[UsageErrorEvent, UsageErrorEvent].publish_error(
            event_error_model=UsageErrorEvent,
            ex=ex,
            step=UsageCancelledEvent.event_type,
            group_id=f"account:{account_usage_entity.account_id}",
            account_id=account_usage_entity.account_id,
            usage_id=account_usage_entity.id,
            usage_type=account_usage_entity.usage_type,
            credits_amount=account_usage_entity.credits_amount,
            pid=pid
        )
        raise
