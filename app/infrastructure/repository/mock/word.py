from __future__ import annotations

from domain.text.word.interfaces.repository import WordRepository
from domain.text.word.entities import WordEntity
from infrastructure.repository.mock.base_repository import BaseMockRepository


class MockWordRepository(BaseMockRepository[WordEntity], WordRepository):
    """
    In-memory mock implementation of WordRepository for testing.
    """

    async def get_by_name_and_language(self, name: str, language_id: int) -> WordEntity | None:
        """
        Find a word by its name and language.
        """
        for word in self.entities.values():
            if word.name == name and word.language_id == language_id:
                return word
        return None

    async def get_many_by_ids(self, ids: list[int]) -> list[WordEntity]:
        """
        Retrieve multiple words by their IDs.
        """
        return [word for word_id, word in self.entities.items() if word_id in ids]
