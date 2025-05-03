from application.account.dtos import AccountDTO
from application.auth.dtos import AuthResponseDTO
from core.di.repository import DIRepository
from core.enums.repository.types import RepositoryTypes
from domain.account.entities import AccountEntity
from domain.auth_profile.interfaces.repository import AuthProfileRepository
from domain.account.interfaces import AccountRepository
from domain.auth_profile.entities import AuthProfileEntity
from application.auth.dtos.password import PasswordRegistrationInitDataDTO, PasswordLoginInitDataDTO, \
    ChangePasswordInitDataDTO
from infrastructure.auth.hashers.password_hasher import password_hasher
from application.security.token import generate_token
from domain.auth_profile.enums import AuthProviderType
from core.messages.exceptions import GetExMessages
from domain.auth_profile.exceptions import AuthProfileAlreadyExistsError, AuthProfileInvalidCredentialsError, \
    AuthProfileNotFoundError, AuthPasswordRegistrationValidationError


class PasswordAuthService:
    def __init__(self, repository_type: RepositoryTypes = RepositoryTypes.TORTOISE):
        self.account_repository = DIRepository.get_repository(AccountRepository, repository_type)()
        self.auth_profile_repository = DIRepository.get_repository(AuthProfileRepository, repository_type)()

    async def register(self, dto: PasswordRegistrationInitDataDTO) -> AuthResponseDTO:
        data = dto.provider_data

        if data.password != data.repeat_password:
            raise AuthPasswordRegistrationValidationError(GetExMessages.wrong_repeat_password(),
                                                          field="repeat_password")

        existing = await self.account_repository.get_by_username(data.username)
        if existing:
            raise AuthProfileAlreadyExistsError(GetExMessages.username_already_exists(data.username), field="username")

        password_hash = password_hasher.hash(data.password)

        account = AccountEntity(
            username=data.username,
            public_name=data.public_name or data.username,
            email=None,
        )
        account = await self.account_repository.save(account)

        profile = AuthProfileEntity(
            account_id=account.id,
            provider_type=AuthProviderType.PASSWORD,
            provider_id=data.username,
            provider_data={"password_hash": password_hash},
            language_code=data.language_code,
        )
        await self.auth_profile_repository.save(profile)

        return AuthResponseDTO(
            token=generate_token(account.id),
            account=AccountDTO.create_from_dict(account.to_dict())
        )

    async def login(self, dto: PasswordLoginInitDataDTO) -> AuthResponseDTO:
        data = dto.provider_data

        profile = await self.auth_profile_repository.get_by_provider_id(data.username, AuthProviderType.PASSWORD)
        if not profile:
            raise AuthProfileInvalidCredentialsError(GetExMessages.invalid_username_or_password(), field="username")

        stored_hash = profile.provider_data.get("password_hash")
        if not password_hasher.verify(data.password, stored_hash):
            raise AuthProfileInvalidCredentialsError(GetExMessages.invalid_username_or_password(), field="password")

        account = await self.account_repository.get_by_id(profile.account_id)

        return AuthResponseDTO(
            token=generate_token(account.id),
            account=AccountDTO.create_from_dict(account.to_dict())
        )

    async def change_password(self, dto: ChangePasswordInitDataDTO, account: AccountEntity) -> AuthResponseDTO:
        profile = await self.auth_profile_repository.get_by_account_id(account.id, AuthProviderType.PASSWORD)

        if not profile:
            raise AuthProfileNotFoundError(GetExMessages.password_auth_profile_not_found())

        profile.provider_data["password_hash"] = password_hasher.hash(dto.provider_data.password)

        await self.auth_profile_repository.save(profile)
        return AuthResponseDTO(
            token=generate_token(account.id),
            account=AccountDTO.create_from_dict(account.to_dict())
        )
