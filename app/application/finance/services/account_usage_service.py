from datetime import datetime, timezone

from core.di.events import DIPublisher
from domain.finance.entities import AccountUsageEntity
from domain.finance.interfaces import AccountUsageRepository
from application.finance.dtos.acount_usage import (
    CreateAccountUsageDTO,
    UpdateAccountUsageDTO,
    AccountUsageDTO,
    AccountUsageListDTO,
)
from application.abstract.services.crud import BaseCRUDService
from core.enums.repository.types import RepositoryTypes
from application.finance.events import UsageCreatedEvent, UsageCancelledEvent, UsageErrorEvent


class AccountUsageService(
    BaseCRUDService[
        AccountUsageEntity,
        AccountUsageRepository,
        AccountUsageDTO,
        AccountUsageListDTO,
        CreateAccountUsageDTO,
        UpdateAccountUsageDTO
    ]
):
    """
    Service for managing account usage of paid AI services.

    Responsibilities:
    - Create usage entries and trigger financial events.
    - Cancel existing usage with timestamp and fire cancellation event.
    """
    entity_class = AccountUsageEntity
    entity_repository_type = AccountUsageRepository
    repository_type = RepositoryTypes.TORTOISE
    create_dto = CreateAccountUsageDTO
    update_dto = UpdateAccountUsageDTO
    item_dto = AccountUsageDTO
    list_dto = AccountUsageListDTO

    async def create(self, entity: AccountUsageEntity) -> AccountUsageEntity:
        """
        Create a new usage record and publish UsageCreatedEvent.

        Args:
            entity (AccountUsageEntity): Usage data to be saved.

        Returns:
            AccountUsageEntity: The saved entity with ID.
        """
        try:
            account_usage_entity: AccountUsageEntity = await super().create(entity)
            await DIPublisher[UsageCreatedEvent].publish(
                payload=UsageCreatedEvent(
                    usage_type=account_usage_entity.usage_type,
                    usage_id=account_usage_entity.id,
                    account_id=account_usage_entity.account_id,
                    credits_amount=account_usage_entity.credits_amount
                ),
                group_id=f"account:{account_usage_entity.account_id}"
            )
            return account_usage_entity
        except Exception as ex:
            await DIPublisher[UsageErrorEvent].publish_error(
                event_error_model=UsageErrorEvent,
                ex=ex,
                step=UsageCreatedEvent.event_type,
                group_id=f"account:{entity.account_id}",
                account_id=entity.account_id,
            )
            raise

    async def cancel(self, account_usage_entity: AccountUsageEntity) -> None:
        """
        Cancel an existing usage entry and trigger UsageCancelledEvent.

        Args:
            account_usage_entity (AccountUsageEntity): Usage to cancel.
        """
        try:
            account_usage_entity.canceled_at = datetime.now(tz=timezone.utc)
            await self.repository.save(account_usage_entity)
            await DIPublisher[UsageCancelledEvent].publish(
                payload=UsageCancelledEvent(
                    account_id=account_usage_entity.account_id,
                    usage_type=account_usage_entity.usage_type,
                    usage_id=account_usage_entity.id,
                    credits_amount=account_usage_entity.credits_amount
                ),
                group_id=f"account:{account_usage_entity.account_id}"
            )
        except Exception as ex:
            await DIPublisher[UsageErrorEvent].publish_error(
                event_error_model=UsageErrorEvent,
                ex=ex,
                step=UsageCancelledEvent.event_type,
                group_id=f"account:{account_usage_entity.account_id}",
                account_id=account_usage_entity.account_id,
            )
            raise
