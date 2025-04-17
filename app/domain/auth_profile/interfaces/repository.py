from __future__ import annotations
from abc import abstractmethod
from domain.auth_profile.entities import AuthProfileEntity
from domain.abstract import EntityRepository
from domain.auth_profile.enums import AuthProviderType


class AuthProfileRepository(EntityRepository[AuthProfileEntity]):
    """
    Interface for working with authorization profile entities in a persistent storage.

    This repository abstracts the data access layer for authorization profiles, which store
    authentication provider metadata (e.g., Telegram, WhatsApp) linked to a user account.

    Methods:
        get_by_provider_id(provider_id: str) -> AuthorizationProfileEntity:
            Fetches an authorization profile using the unique provider identifier.
            Should raise AuthorizationProfileNotFoundError if not found.
    """

    @abstractmethod
    async def get_by_provider_id(self, provider_id: str, provider_type: AuthProviderType) -> AuthProfileEntity | None:
        """
        Retrieve an authorization profile by its external provider ID.

        Args:
            provider_id (str): Unique identifier assigned by the provider (e.g., Telegram user ID).
            :param provider_id:
            :param provider_type:

        Returns:
            AuthorizationProfileEntity | None: Matching profile entity or None if not found.
        """
        ...

    @abstractmethod
    async def get_list_by_account_id(self, account_id: int) -> list[AuthProfileEntity]:
        ...

    @abstractmethod
    async def get_by_account_id(self, account_id: int, provider_type: AuthProviderType) -> AuthProfileEntity | None:
        ...
