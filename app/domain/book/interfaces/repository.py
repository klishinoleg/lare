from __future__ import annotations

from abc import abstractmethod
from domain.abstract import EntityRepository
from domain.book.entities import ChapterEntity, BookEntity


class BookRepository(EntityRepository[BookEntity]):
    """
    Abstract repository interface for Book entities.
    """

    @abstractmethod
    async def get_by_account(self, account_id: int) -> list[BookEntity]:
        ...


class ChapterRepository(EntityRepository[ChapterEntity]):
    """
    Abstract repository interface for Chapter entities.
    """

    @abstractmethod
    async def get_by_book(self, book_id: int, account_id: int) -> list[ChapterEntity]:
        ...
