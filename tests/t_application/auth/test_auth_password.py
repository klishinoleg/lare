import pytest

from application.access_control.services import Accessor
from application.access_control.services.user_creator_service import UserCreatorService
from application.auth.dtos.password import PasswordRegistrationInitDataDTO, PasswordLoginInitDataDTO, \
    ChangePasswordInitDataDTO
from application.auth.services.password_auth_service import PasswordAuthService
from application.security.token import verify_token
from core.di.repository import DIRepository
from core.enums.repository.types import RepositoryTypes
from core.messages.exceptions import GetExMessages
from domain.access_role.enums.roles import AccessRole
from domain.access_role.interfaces.repository import AccessRoleRepository
from domain.account.entities import AccountEntity
from domain.auth_profile.exceptions import AuthPasswordRegistrationValidationError, AuthProfileInvalidCredentialsError, \
    AuthProfileAlreadyExistsError
from tests.t_infrastructure.auth.factory.password import PasswordRegistrationInitDataDTOFactory, \
    PasswordLoginInitDataDTOFactory, ChangePasswordInitDataDTOFactory


class TestAuthPassword:
    @pytest.fixture(scope="module")
    def service(self) -> PasswordAuthService:
        return PasswordAuthService(RepositoryTypes.MOCK)

    @pytest.mark.asyncio
    async def test_password_registration(self, service: PasswordAuthService) -> None:
        registration_init_dto: PasswordRegistrationInitDataDTO = PasswordRegistrationInitDataDTOFactory()
        registration_data = await service.register(registration_init_dto)
        user_id_from_token = verify_token(registration_data.token)
        assert registration_data.account.username == registration_init_dto.provider_data.username
        assert registration_data.account.public_name == registration_init_dto.provider_data.public_name
        assert user_id_from_token == registration_data.account.id

    @pytest.mark.asyncio
    async def test_password_login(self, service: PasswordAuthService) -> None:
        registration_init_dto: PasswordRegistrationInitDataDTO = PasswordRegistrationInitDataDTOFactory()
        registration_data = await service.register(registration_init_dto)
        login_init_dto: PasswordLoginInitDataDTO = PasswordLoginInitDataDTOFactory(
            provider_data__username=registration_data.account.username,
            provider_data__password=registration_init_dto.provider_data.password
        )
        login_data = await service.login(login_init_dto)
        user_id_from_token = verify_token(login_data.token)
        assert user_id_from_token == registration_data.account.id

    @pytest.mark.asyncio
    async def test_password_change(self, service: PasswordAuthService) -> None:
        registration_init_dto: PasswordRegistrationInitDataDTO = PasswordRegistrationInitDataDTOFactory()
        registration_data = await service.register(registration_init_dto)
        change_password_init: ChangePasswordInitDataDTO = ChangePasswordInitDataDTOFactory()
        await service.change_password(change_password_init,
                                      AccountEntity(**registration_data.account.model_dump()))
        login_init_dto: PasswordLoginInitDataDTO = PasswordLoginInitDataDTOFactory(
            provider_data__username=registration_data.account.username,
            provider_data__password=change_password_init.provider_data.password
        )
        login_data = await service.login(login_init_dto)
        user_id_from_token = verify_token(login_data.token)
        assert user_id_from_token == registration_data.account.id
        login_init_dto.provider_data.password = registration_init_dto.provider_data.password
        with pytest.raises(AuthProfileInvalidCredentialsError, match=GetExMessages.invalid_username_or_password()):
            await service.login(login_init_dto)

    @pytest.mark.asyncio
    async def test_wrong_repear_password(self, service: PasswordAuthService) -> None:
        registration_init_dto: PasswordRegistrationInitDataDTO = PasswordRegistrationInitDataDTOFactory(
            provider_data__repeat_password="wront_repeat_password"
        )
        with pytest.raises(AuthPasswordRegistrationValidationError, match=GetExMessages.wrong_repeat_password()):
            await service.register(registration_init_dto)

    @pytest.mark.asyncio
    async def test_wrong_login_credentials(self, service: PasswordAuthService) -> None:
        registration_init_dto: PasswordRegistrationInitDataDTO = PasswordRegistrationInitDataDTOFactory()
        await service.register(registration_init_dto)
        login_init_dto: PasswordLoginInitDataDTO = PasswordLoginInitDataDTOFactory(
            provider_data__username=registration_init_dto.provider_data.username
        )
        with pytest.raises(AuthProfileInvalidCredentialsError, match=GetExMessages.invalid_username_or_password()):
            await service.login(login_init_dto)

    @pytest.mark.asyncio
    async def test_wrong_username(self, service: PasswordAuthService) -> None:
        registration_init_dto: PasswordRegistrationInitDataDTO = PasswordRegistrationInitDataDTOFactory()
        await service.register(registration_init_dto)
        with pytest.raises(AuthProfileAlreadyExistsError,
                           match=GetExMessages.username_already_exists(registration_init_dto.provider_data.username)):
            await service.register(registration_init_dto)

    @pytest.mark.asyncio
    async def test_superuser(self) -> None:
        superuser = await UserCreatorService.create_superuser(username="superuser", password="passw",
                                                              public_name="Super User",
                                                              repository_type=RepositoryTypes.MOCK)
        Accessor.role_repository = DIRepository.get_repository(AccessRoleRepository, RepositoryTypes.MOCK)()
        assert await Accessor.has_role(superuser, AccessRole.SUPERUSER)
        assert await Accessor.has_role(superuser, AccessRole.ADMINISTRATOR)
        assert await Accessor.has_role(superuser, AccessRole.NOT_ROLE)
