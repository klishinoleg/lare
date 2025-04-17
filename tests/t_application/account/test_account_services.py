import pytest
from application.account.services import AccountService
from domain.account.interfaces import AccountRepository
from domain.account.exceptions import NotUniqueUsernameError
from core.messages.exceptions import GetExMessages
from tests.t_domain.entities.account import AccountFactory
from tests.t_application.abstract.base_test_crud import BaseCRUDServiceTest


class TestAccountService(BaseCRUDServiceTest):
    init_service_type = AccountService
    init_entity_repository = AccountRepository
    factory = staticmethod(AccountFactory)
    _field_for_update = "username"

    @pytest.mark.asyncio
    async def test_check_username_uniqueness(self):
        entity = self.factory()
        await self._service.create(entity)

        with pytest.raises(NotUniqueUsernameError, match=GetExMessages.username_already_exists(entity.username)):
            await self._service._create_validate__check_username(entity)
