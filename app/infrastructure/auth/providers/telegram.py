from __future__ import annotations
from core.messages.exceptions import GetExMessages
from domain.auth_profile.entities import AuthProfileEntity
from domain.auth_profile.enums import AuthProviderType
from domain.auth_profile.interfaces.provider import BaseAuthProvider
from domain.auth_profile.exceptions import AuthProfileInvalidCredentialsError
from infrastructure.auth.dtos.telegram import TelegramProviderDataDTO
from infrastructure.auth.utils.telegram import validate_telegram_init_data


class TelegramAuthProvider(BaseAuthProvider):
    """
    Infrastructure implementation of Telegram authentication via WebApp initData.
    Validates the provided hash and constructs an AuthProfileEntity.
    """

    @classmethod
    def provider_type(cls) -> AuthProviderType:
        return AuthProviderType.TELEGRAM

    @staticmethod
    def get_language_code(provider_data: TelegramProviderDataDTO) -> str | None:
        return provider_data.init_data_unsafe.user.language_code

    @staticmethod
    def get_public_name(provider_data: TelegramProviderDataDTO) -> str | None:
        user = provider_data.init_data_unsafe.user
        return f"{user.first_name} {user.last_name}".strip()

    @staticmethod
    def get_username(provider_data: TelegramProviderDataDTO) -> str:
        user = provider_data.init_data_unsafe.user
        return f"TG:{user.id}:{user.username}".strip()

    async def validate_and_parse(self, provider_data: TelegramProviderDataDTO) -> AuthProfileEntity:
        """
        Validate Telegram WebApp init data using bot token and HMAC check.

        Args:
            provider_data: TelegramProviderDataDTO

        Returns:
            AuthProfileEntity: Validated profile

        Raises:
            AuthProfileInvalidCredentialsError: If hash or auth_date is invalid.
        """

        if not validate_telegram_init_data(provider_data):
            raise AuthProfileInvalidCredentialsError(GetExMessages.telegram_invalid_hash(), field="hash")

        data = provider_data.init_data_unsafe.model_dump()

        user = data.get("user", {})
        provider_id = str(user.get("id"))

        return AuthProfileEntity(
            account_id=0,
            provider_type=AuthProviderType.TELEGRAM,
            provider_id=provider_id,
            provider_data=provider_data.init_data_unsafe.model_dump(),
            language_code=self.get_language_code(provider_data),
        )
