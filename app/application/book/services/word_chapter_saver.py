from typing import List
from application.book.services.book_crud_service import BookService
from core.di.repository import DIRepository
from core.enums.repository.types import RepositoryTypes
from domain.book.entities import ChapterEntity
from domain.text.word.entities import WordEntity
from domain.text.word_chapter.entities import WordChapterEntity
from application.book.datatypes.chapter_content import ChapterContentWordType
from domain.text.word.interfaces.repository import WordRepository
from domain.text.word_chapter.interfaces.repository import WordChapterRepository
from domain.text.word_chapter.exceptions import WordChapterEntityNotFound


class WordChapterSaverService:
    """
    Service for saving parsed chapter words into database using repositories.
    """

    def __init__(self, repository_type: RepositoryTypes = RepositoryTypes.TORTOISE):
        self.word_repo: WordRepository = DIRepository.get_repository(WordRepository, repository_type)()
        self.word_chapter_repo: WordChapterRepository = DIRepository.get_repository(WordChapterRepository,
                                                                                    repository_type)()
        self.book_service = BookService(repository_type)

    async def get_by_id(self, word_chapter_id: int) -> WordChapterEntity:
        o = await self.word_chapter_repo.get_by_id(word_chapter_id)
        if not o:
            raise WordChapterEntityNotFound
        return o

    async def update_segment(self, word_chapter_id: int, segment_id: int) -> WordChapterEntity:
        word_chapter_entity = await self.get_by_id(word_chapter_id)
        word_chapter_entity.segment_id = segment_id
        return await self.word_chapter_repo.save(word_chapter_entity)

    async def update_phrase(self, word_chapter_id: int, phrase_id: int) -> WordChapterEntity:
        word_chapter_entity = await self.get_by_id(word_chapter_id)
        word_chapter_entity.phrase_id = phrase_id
        return await self.word_chapter_repo.save(word_chapter_entity)

    async def save_words_from_chapter_content(
            self,
            chapter: ChapterEntity,
            content: List[ChapterContentWordType],
    ) -> None:
        """
        Save parsed chapter content words into Word and WordChapterEntity tables.

        Args:
            chapter (ChapterEntity): The ID of the chapter.
            content (List[ChapterContentType]): The parsed chapter content.
        """

        position_counter = 0
        book_entity = await self.book_service.get_by_id(id=chapter.book_id)
        for word_data in content:
            await self._save_single_word(word_data, chapter.id, book_entity.language_id, position_counter)
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

        word_chapter = WordChapterEntity(
            name=word_data.origin,
            word_id=word.id,
            chapter_id=chapter_id,
            position=position,
            n=min(word_data.lines, 3)
        )

        await self.word_chapter_repo.save(word_chapter)
