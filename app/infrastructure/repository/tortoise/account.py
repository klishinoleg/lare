from __future__ import annotations
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models import AccountModel
from domain.account.entities import AccountEntity


class TortoiseAccountRepository(BaseTortoiseRepository[AccountEntity, AccountModel]):
    """
    Concrete repository implementation for the Account entity using Tortoise ORM.

    This class translates between the Tortoise ORM model and the domain entity,
    and provides database-level operations such as querying by username and updating credits.

    Inherits:
        BaseTortoiseRepository[AccountEntity, AccountModel]: Base class for Tortoise repositories.

    Attributes:
        model (Type[AccountModel]): The ORM model class used for database operations.
    """

    model = AccountModel

    @staticmethod
    async def to_entity(o: AccountModel) -> AccountEntity:
        """
        Convert an AccountModel instance to a domain-level AccountEntity.

        Args:
            o (AccountModel): The ORM model instance.

        Returns:
            AccountEntity: The domain entity version of the model.
        """
        return AccountEntity(
            id=o.id,
            username=o.username,
            credits=o.credits,
            public_name=o.public_name,
            email=o.email,
            is_active=o.is_active,
            updated_at=o.updated_at,
            created_at=o.created_at
        )

    async def get_by_username(self, username: str) -> AccountEntity | None:
        """
        Retrieve an account by its username.

        Args:
            username (str): The unique username to search for.

        Returns:
            AccountEntity | None: The corresponding entity if found, otherwise None.
        """
        account = await self.model.get_or_none(username=username)
        if not account:
            return None
        return await self.to_entity(account)

    async def update_credits(self, account_id: int, new_credits: float) -> AccountEntity | None:
        """
        Update the credit balance for a given account ID.

        Args:
            account_id (int): ID of the account to update.
            new_credits (float): The new credits value.

        Returns:
            AccountEntity | None: The updated entity, or None if not found.
        """
        account = await self.model.get_or_none(id=account_id)
        if account:
            account.credits = new_credits
            await account.save()
            return await self.to_entity(account)
        return None
