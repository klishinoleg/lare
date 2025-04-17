from __future__ import annotations
from infrastructure.repository.mock.base_repository import BaseMockRepository
from domain.account.entities import AccountEntity


class MockAccountRepository(BaseMockRepository[AccountEntity]):
    """
    In-memory mock implementation of AccountRepository for testing purposes.

    This class simulates account persistence and retrieval without using a real database.
    It is useful in unit tests and development environments.

    Inherits:
        BaseMockRepository[AccountEntity]: Base class with CRUD simulation logic.

    Methods:
        get_by_username(username: str) -> AccountEntity | None:
            Returns the first account entity matching the given username.

        update_credits(account_id: int, new_credits: float) -> AccountEntity | None:
            Updates the account's credit value and saves the entity in memory.
    """

    async def get_by_username(self, username: str) -> AccountEntity | None:
        """
        Retrieve an account by username.

        Args:
            username (str): The username to search for.

        Returns:
            AccountEntity | None: The matching entity, or None if not found.
        """
        return next((e for e in self.entities.values() if e.username == username), None)

    async def update_credits(self, account_id: int, new_credits: float) -> AccountEntity | None:
        """
        Update the credit value of the account with the given ID.

        Args:
            account_id (int): ID of the account to update.
            new_credits (float): New credit value to assign.

        Returns:
            AccountEntity | None: The updated account, or None if not found.
        """
        account = await self.get_by_id(account_id)
        if account:
            account.credits = new_credits
            return await self.save(account)
        return account
