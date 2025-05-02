from __future__ import annotations
from infrastructure.repository.mock.base_repository import BaseMockRepository
from domain.book.entities import BookEntity
from domain.book.interfaces.repository import BookRepository


class MockBookRepository(BaseMockRepository[BookEntity], BookRepository):
    """
    In-memory mock implementation of BookRepository for testing purposes.

    This class simulates book persistence and retrieval with support for
    chapters count and account filtering.
    """

    async def get_by_account(self, account_id: int) -> list[BookEntity]:
        """
        Get all books belonging to a specific account.

        Args:
            account_id (int): The ID of the account.

        Returns:
            list[BookEntity]: All books owned by the given account.
        """
        return [b for b in self.entities.values() if b.account_id == account_id]
