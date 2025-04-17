from application.security.token import generate_token
from core.enums.repository.types import RepositoryTypes
from core.di.repository import DIRepository
from domain.account.interfaces import AccountRepository
from domain.auth_profile.factories.provider_factory import AuthProviderFactory
from application.auth.dtos import AuthInitDataDTO, AuthResponseDTO, AUIDDTO, AuthProfileDTO
from domain.account.entities import AccountEntity
from application.account.dtos import AccountDTO
from domain.auth_profile.interfaces.repository import AuthProfileRepository


class AuthViaProfileService:
    """
    Service responsible for authenticating users via external profiles (e.g. Telegram).

    If a profile already exists, it fetches the linked account and returns it.
    Otherwise, creates a new account and profile, then returns a token and account.
    """

    def __init__(
            self,
            repository_type: RepositoryTypes = RepositoryTypes.TORTOISE
    ):
        self.account_repository = DIRepository.get_repository(AccountRepository, repository_type)()
        self.auth_profile_repository = DIRepository.get_repository(AuthProfileRepository, repository_type)()

    async def get_profiles(self, account_id: int) -> list[AuthProfileDTO]:
        profiles = await self.auth_profile_repository.get_list_by_account_id(account_id=account_id)
        return [
            AuthProfileDTO.create_from_dict(o.to_dict())
            for o in profiles
        ]

    async def authenticate(self, dto: AUIDDTO) -> AuthResponseDTO:
        """
        Authenticate user based on profile provider data.

        Steps:
        - Validate provider data and convert to AuthProfileEntity
        - Check if profile exists → get account
        - Else: create account + save profile
        - Return token + account DTO

        Args:
            dto (AuthInitDataDTO): Incoming data containing provider type and init data.

        Returns:
            AuthResponseDTO: Auth token + user data.
        """
        provider = AuthProviderFactory.get_provider(dto.provider_type)
        profile_entity = await provider.validate_and_parse(dto.provider_data)

        existing_profile = await self.auth_profile_repository.get_by_provider_id(
            profile_entity.provider_id,
            dto.provider_type
        )

        if existing_profile:
            account = await self.account_repository.get_by_id(existing_profile.account_id)
        else:
            account = AccountEntity(
                username=provider.get_username(dto.provider_data),
                public_name=provider.get_public_name(dto.provider_data),
                email=None,
            )
            account = await self.account_repository.save(account)
            profile_entity.account_id = account.id
            await self.auth_profile_repository.save(profile_entity)

        token = generate_token(account.id)

        return AuthResponseDTO(
            token=token,
            account=AccountDTO.create_from_dict(account.to_dict())
        )
