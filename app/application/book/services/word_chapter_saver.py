from typing import List

from core.di.repository import DIRepository
from core.enums.repository.types import RepositoryTypes
from domain.word.entities import WordEntity
from domain.word_chapter.entities import WordChapter
from application.book.datatypes.chapter_content import ChapterContentType, ChapterContentWordType
from domain.word.interfaces.repository import WordRepository
from domain.word_chapter.interfaces.repository import WordChapterRepository


class WordChapterSaverService:
    """
    Service for saving parsed chapter words into database using repositories.
    """

    def __init__(self, repository_type: RepositoryTypes = RepositoryTypes.TORTOISE):
        self.word_repo = DIRepository.get_repository(WordRepository, repository_type)
        self.word_chapter_repo = DIRepository.get_repository(WordChapterRepository, repository_type)

    async def save_words_from_chapter_content(
            self,
            chapter_id: int,
            language_id: int,
            content: List[ChapterContentType],
    ) -> None:
        """
        Save parsed chapter content words into Word and WordChapter tables.

        Args:
            chapter_id (int): The ID of the chapter.
            language_id (int): The language ID for words.
            content (List[ChapterContentType]): The parsed chapter content.
        """

        position_counter = 0

        for chapter in content:
            for word_data in chapter.words:
                await self._save_single_word(word_data, chapter_id, language_id, position_counter)
                position_counter += 1

    async def _save_single_word(
            self,
            word_data: ChapterContentWordType,
            chapter_id: int,
            language_id: int,
            position: int,
    ) -> None:
        """
        Save a single word and its link to a chapter.
        """
        normalized_name = word_data.base.upper()

        word = await self.word_repo.get_by_name_and_language(name=normalized_name, language_id=language_id)
        if not word:
            word_entity = WordEntity(name=normalized_name, language_id=language_id)
            word = await self.word_repo.save(word_entity)

        word_chapter = WordChapter(
            name=word_data.origin,
            word_id=word.id,
            chapter_id=chapter_id,
            position=position,
            n=min(word_data.lines, 3)
        )

        await self.word_chapter_repo.save(word_chapter)
