from __future__ import annotations
from abc import ABC, abstractmethod
from pydantic import BaseModel
from domain.auth_profile.entities import AuthProfileEntity
from domain.auth_profile.enums import AuthProviderType


class BaseAuthProvider[BM: BaseModel](ABC):
    """
    Abstract base class for external authentication providers (e.g. Telegram, WhatsApp, etc.).

    This interface defines how to extract and validate identity data from third-party providers,
    and how to convert it into a consistent AuthorizationProfileEntity that can be persisted
    and associated with a user account.

    Responsibilities:
    - Validate incoming provider data (e.g. Telegram initData or OAuth tokens)
    - Convert valid data into a domain-level AuthorizationProfileEntity
    - Report its own provider type for dynamic registration and resolution

    Implementations should raise exceptions if validation fails or data is malformed.
    """

    @classmethod
    @abstractmethod
    def provider_type(cls) -> AuthProviderType:
        """
        Returns the type of the authorization provider this class implements.

        Returns:
            AuthProviderType: Enum representing the provider (e.g., TELEGRAM).
        """
        ...

    @abstractmethod
    async def validate_and_parse(
            self, provider_data: dict, is_safe: bool = False
    ) -> AuthProfileEntity:
        """
        Validate and parse raw provider data into an AuthorizationProfileEntity.

        Args:
            provider_data (dict): Raw data received from the external auth provider.

        Returns:
            AuthorizationProfileEntity: A validated domain entity.

        Raises:
            AuthorizationProfileInvalidCredentialsError: If data is invalid or verification fails.
            :param provider_data:
            :param is_safe:
        """
        ...

    @staticmethod
    @abstractmethod
    def get_public_name(provider_data: BM) -> str | None:
        ...

    @staticmethod
    @abstractmethod
    def get_username(provider_data: BM) -> str:
        ...

    @staticmethod
    @abstractmethod
    def get_language_code(provider_data: BM) -> str | None:
        ...
