from __future__ import annotations
from domain.auth_profile.entities import AuthProfileEntity
from domain.auth_profile.enums import AuthProviderType
from domain.auth_profile.interfaces.repository import AuthProfileRepository
from infrastructure.repository.mock.base_repository import BaseMockRepository


class MockAuthProfileRepository(BaseMockRepository[AuthProfileEntity], AuthProfileRepository):
    """
    In-memory mock repository for testing authentication profiles.

    Provides fake storage and lookup logic for use in unit tests or dev environments.
    """

    async def get_by_provider_id(self, provider_id: str, provider_type: AuthProviderType) -> AuthProfileEntity | None:
        """
        Retrieve an auth profile by external provider ID and type.

        Args:
            provider_id (str): External system's unique user ID.
            provider_type (AuthProviderType): Type of auth provider (e.g., TELEGRAM).

        Returns:
            AuthProfileEntity | None: Matching entity or None.
        """
        return next(
            (
                e for e in self.entities.values()
                if e.provider_id == provider_id and e.provider_type == provider_type
            ),
            None
        )

    async def get_list_by_account_id(self, account_id: int) -> list[AuthProfileEntity]:
        return [
            e for e in self.entities.values()
            if e.account_id == account_id
        ]

    async def get_by_account_id(self, account_id: int, provider_type: AuthProviderType) -> AuthProfileEntity | None:
        return next(
            e for e in self.entities.values()
            if e.account_id == account_id and e.provider_type == provider_type
        )
