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
