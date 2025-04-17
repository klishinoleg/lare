from __future__ import annotations
from abc import abstractmethod
from domain.account.entities import AccountEntity
from domain.abstract import EntityRepository


class AccountRepository(EntityRepository[AccountEntity]):
    """
    Abstract repository interface for Account entities.

    This repository defines the operations that can be performed
    on Account objects in the persistence layer. Concrete implementations
    may use different backends (e.g., Tortoise ORM, Redis, in-memory, etc.).

    Inherits:
        EntityRepository[AccountEntity]: Generic CRUD operations.

    Methods:
        get_by_username(username: str) -> AccountEntity | None:
            Retrieve an account by its unique username.

        update_credits(account_id: int, new_credits: float) -> AccountEntity | None:
            Update the user's credit balance and return the updated entity.
    """

    @abstractmethod
    async def get_by_username(self, username: str) -> AccountEntity | None:
        """
        Retrieve an account by its unique username.

        Args:
            username (str): The username to search for.

        Returns:
            AccountEntity | None: The matching account or None if not found.
        """
        ...

    @abstractmethod
    async def update_credits(self, account_id: int, new_credits: float) -> AccountEntity | None:
        """
        Update the credit balance of an account.

        Args:
            account_id (int): The ID of the account to update.
            new_credits (float): The new credit value to set.

        Returns:
            AccountEntity | None: The updated account, or None if not found.
        """
        ...
