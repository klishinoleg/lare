import pytest
from application.security.token import verify_token
from core.config import settings
from core.enums.repository.types import RepositoryTypes
from application.auth.services.auth_via_profile import AuthViaProfileService
from domain.auth_profile.exceptions import AuthProfileInvalidCredentialsError
from core.registrators.init_auth_providers import register_auth_providers
from tests.t_infrastructure.auth.factory.telegram import create_fake_telegram_provider_data
from infrastructure.auth.dtos.telegram import TelegramAuthInitDataDTO
from domain.auth_profile.enums import AuthProviderType


class TestAuthTelegram:
    @pytest.fixture(scope="module")
    def service(self) -> AuthViaProfileService:
        register_auth_providers()
        settings.secret_key = "test_secret_key"
        return AuthViaProfileService(RepositoryTypes.MOCK)

    @pytest.mark.asyncio
    async def test_provider_data(self, service: AuthViaProfileService) -> None:
        fake_init_data = create_fake_telegram_provider_data()
        auth_init_data = TelegramAuthInitDataDTO(
            provider_type=AuthProviderType.TELEGRAM,
            provider_data=fake_init_data,
        )
        auth = await service.authenticate(auth_init_data)
        user_id_from_token = verify_token(auth.token)
        fake_user = fake_init_data.init_data_unsafe.user
        assert auth.account.username == f"TG:{fake_user.id}:{fake_user.username}".strip()
        assert auth.account.public_name == f"{fake_user.first_name} {fake_user.last_name}".strip()
        assert user_id_from_token == auth.account.id
        profiles = await service.get_profiles(account_id=auth.account.id)
        assert len(profiles) == 1
        assert profiles[0].provider_type == AuthProviderType.TELEGRAM
        assert profiles[0].language_code == fake_user.language_code

    @pytest.mark.asyncio
    async def test_bad_provided_data(self, service: AuthViaProfileService) -> None:
        fake_init_data = create_fake_telegram_provider_data()
        fake_init_data.init_data = fake_init_data.init_data.replace("hash=", "hash=a")
        auth_init_data = TelegramAuthInitDataDTO(
            provider_type=AuthProviderType.TELEGRAM,
            provider_data=fake_init_data,
        )
        with pytest.raises(AuthProfileInvalidCredentialsError, match="Invalid Telegram hash"):
            await service.authenticate(auth_init_data)
