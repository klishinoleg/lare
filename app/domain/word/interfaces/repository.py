from __future__ import annotations
from abc import abstractmethod
from domain.abstract import EntityRepository
from domain.word.entities import WordEntity


class WordRepository(EntityRepository[WordEntity]):
    """
    Abstract repository interface for Word entities.
    """

    @abstractmethod
    async def get_by_name_and_language(self, name: str, language_id: int) -> WordEntity | None:
        """
        Retrieve a word by its name and language.
        """
        ...

    @abstractmethod
    async def get_many_by_ids(self, ids: list[int]) -> list[WordEntity]:
        """
        Retrieve multiple words by a list of IDs.
        """
        ...
