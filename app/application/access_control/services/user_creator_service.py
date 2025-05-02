from core.enums.repository.types import RepositoryTypes
from application.auth.services.password_auth_service import PasswordAuthService
from application.auth.dtos.password import PasswordRegistrationInitDataDTO, PasswordRegistrationDTO
from domain.access_role.enums.roles import AccessRole
from domain.auth_profile.enums import AuthProviderType
from domain.access_role.interfaces.repository import AccessRoleRepository
from domain.access_role.entities import AccessRoleEntity
from core.di.repository import DIRepository
from domain.account.entities import AccountEntity


class UserCreatorService:
    @staticmethod
    async def create_superuser(
            username: str, password: str, public_name: str, language_code: str = "en",
            repository_type: RepositoryTypes = RepositoryTypes.TORTOISE) -> AccountEntity:
        access_role_repository = DIRepository.get_repository(AccessRoleRepository, repository_type)()
        password_auth_service = PasswordAuthService(repository_type=repository_type)
        user_data = PasswordRegistrationDTO(
            username=username,
            password=password,
            repeat_password=password,
            language_code=language_code,
            public_name=public_name
        )
        init_data = PasswordRegistrationInitDataDTO(
            provider_data=user_data, provider_type=AuthProviderType.PASSWORD
        )
        registration_data = await password_auth_service.register(init_data)
        account = registration_data.account
        access_role = AccessRoleEntity(
            account_id=account.id,
            role=AccessRole.SUPERUSER
        )
        access_role = await access_role_repository.save(access_role)
        return AccountEntity(**account.model_dump())
