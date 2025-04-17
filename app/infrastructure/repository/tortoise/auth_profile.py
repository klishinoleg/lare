from __future__ import annotations
from domain.auth_profile.enums import AuthProviderType
from domain.auth_profile.entities import AuthProfileEntity
from domain.auth_profile.interfaces.repository import AuthProfileRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models.auth_profil import AuthProfileModel


class TortoiseAuthProfileRepository(BaseTortoiseRepository[AuthProfileEntity, AuthProfileModel], AuthProfileRepository):
    """
    Tortoise ORM repository for managing authentication profiles.

    Provides methods to retrieve and store third-party authentication profiles (e.g., Telegram).
    Implements the AuthProfileRepository interface for the domain layer.
    """

    model = AuthProfileModel

    @staticmethod
    async def to_entity(o: AuthProfileModel) -> AuthProfileEntity:
        """
        Convert ORM model to domain entity.

        Args:
            o (AuthProfileModel): ORM model instance.

        Returns:
            AuthProfileEntity: The corresponding domain entity.
        """
        return AuthProfileEntity(
            id=o.id,
            account_id=getattr(o, "account_id"),
            provider_type=o.provider_type,
            provider_id=o.provider_id,
            provider_data=o.provider_data,
            created_at=o.created_at,
            updated_at=o.updated_at,
            language_code=o.language_code
        )

    async def get_by_provider_id(self, provider_id: str, provider_type: AuthProviderType) -> AuthProfileEntity | None:
        """
        Find an auth profile by provider ID.

        Args:
            :param provider_id:
            :param provider_type:
            provider_id (str): External service's user ID (e.g., Telegram ID).

        Returns:
            AuthProfileEntity | None: Found entity or None.
        """
        profile = await self.model.get_or_none(provider_type=provider_type, provider_id=provider_id)
        return await self.to_entity(profile) if profile else None

    async def get_list_by_account_id(self, account_id: int) -> list[AuthProfileEntity]:
        return [await self.to_entity(o) for o in await self.model.filter(account_id=account_id).all()]

    async def get_by_account_id(self, account_id: int, provider_type: AuthProviderType) -> AuthProfileEntity | None:
        return await self.to_entity(await self.model.filter(account_id=account_id, provider_type=provider_type).first())
