from __future__ import annotations
from abc import abstractmethod

from domain.abstract import EntityRepository
from domain.text_data.word.entities import WordTranslateEntity, WordVoiceEntity


class WordTranslateRepository(EntityRepository[WordTranslateEntity]):
    """
    Repository interface for word translation records.
    """

    @abstractmethod
    async def get_by_word(self, word_id: int, language_id: int, account_id: int) -> WordTranslateEntity | None:
        """
        Retrieve translation for a specific word, language, and account.
        """
        ...


class WordVoiceRepository(EntityRepository[WordVoiceEntity]):
    """
    Repository interface for word voice records.
    """

    @abstractmethod
    async def get_by_word(self, word_id: int) -> WordVoiceEntity | None:
        """
        Retrieve the voice record for a given word.
        """
        ...
