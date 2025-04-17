from __future__ import annotations
from typing import TypeVar

from application.access_control.services import Accessor
from application.access_control.validators.self_access_validator import SelfAccessValidator
from domain.account.entities import AccountEntity
from domain.account.exceptions import AccountNotFoundError, NotUniqueUsernameError, AccountPermissionDenied
from domain.account.interfaces import AccountRepository
from application.abstract.services.crud import BaseCRUDService
from application.account.dtos import AccountDTO, AccountListDTO
from core.messages.exceptions import GetExMessages

AR = TypeVar('AR', bound=AccountRepository)


class AccountService(BaseCRUDService[AccountEntity]):
    entity_class = AccountEntity
    list_dto = AccountListDTO
    item_dto = AccountDTO
    not_found_exception = AccountNotFoundError
    entity_repository_type = AccountRepository
    entity_permission_denied_exception = AccountPermissionDenied

    async def _create_validate__check_username(self, entity: AccountEntity):
        res = await self.repository.get_by_username(username=entity.username)
        if res:
            raise NotUniqueUsernameError(GetExMessages.username_already_exists(entity.username), field="username")

    async def get_by_username(self, username: str):
        return await self.repository.get_by_username(username=username)

    def _set_acces_control_validators(self):
        Accessor.register(self.entity_class, SelfAccessValidator(), self.entity_permission_denied_exception)
