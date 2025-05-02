from __future__ import annotations
from application.access_control.services import Accessor
from application.access_control.validators.self_access_validator import SelfAccessValidator
from core.di.repository import DIRepository
from domain.account.entities import AccountEntity
from domain.account.exceptions import AccountNotFoundError, NotUniqueUsernameError, AccountPermissionDenied
from domain.account.interfaces import AccountRepository
from application.abstract.services.crud import BaseCRUDService
from application.account.dtos import AccountDTO, AccountListDTO, UpdateAccountDTO, CreateAccountDTO
from core.messages.exceptions import GetExMessages
from domain.auth_profile.entities import AuthProfileEntity
from domain.auth_profile.enums import AuthProviderType
from domain.auth_profile.interfaces.repository import AuthProfileRepository


class AccountService(
    BaseCRUDService[AccountEntity, AccountRepository, AccountDTO, AccountListDTO, CreateAccountDTO, UpdateAccountDTO]
):
    entity_class = AccountEntity
    list_dto = AccountListDTO
    item_dto = AccountDTO
    not_found_exception = AccountNotFoundError
    entity_repository_type = AccountRepository
    entity_permission_denied_exception = AccountPermissionDenied

    async def _create_validate__check_username(self, entity: AccountEntity) -> None:
        res = await self.repository.get_by_username(username=entity.username)
        if res:
            raise NotUniqueUsernameError(GetExMessages.username_already_exists(entity.username), field="username")

    async def get_by_username(self, username: str) -> AccountEntity | None:
        return await self.repository.get_by_username(username=username)

    def _set_acces_control_validators(self) -> None:
        Accessor.register(self.entity_class, SelfAccessValidator(), self.entity_permission_denied_exception)

    @staticmethod
    async def get_auth_profile_by_auth_provider(
            account_id: int,
            auth_provider: AuthProviderType) -> AuthProfileEntity | None:
        auth_profile_repository: AuthProfileRepository = DIRepository().get_repository(AuthProfileRepository)()
        return await auth_profile_repository.get_by_account_id(account_id, auth_provider)
