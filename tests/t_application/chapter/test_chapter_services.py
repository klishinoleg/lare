from __future__ import annotations
import re
import pytest
from application.book.datatypes.chapter_content import ChapterContentWordType
from application.book.services.chapter_crud_service import ChapterService
from application.book.utils.text_processing import process_text_to_chapters
from domain.book.entities import ChapterEntity
from domain.book.interfaces.repository import ChapterRepository
from tests.t_application.abstract.base_test_crud import BaseCRUDServiceTest
from tests.t_domain.entities.chapter import ChapterFactory
from application.book.services.word_chapter_saver import WordChapterSaverService


class TestChapterService(BaseCRUDServiceTest[ChapterEntity, ChapterRepository, ChapterService, ChapterFactory]):
    init_service_type = ChapterService
    init_entity_repository = ChapterRepository
    factory = ChapterFactory
    _account = None

    async def _get_fake_entity(self, **kwargs: dict) -> ChapterEntity:
        main_account = await self._get_main_account()
        return await super()._get_fake_entity(account_id=main_account.id, book_id=1)  # type: ignore[arg-type]

    @pytest.fixture()
    def text(self) -> str:
        return """
    Chapter 1: "The Strange 'Adventure' – A Beginning"
    “This,” said John, “is the start — the real ‘beginning’!”
    He looked around: ‘clouds’, ‘winds’ — and «secrets» — were everywhere.
    “Is it... possible?” she asked — nervously.

    John replied: "Indeed... It’s possible! Absolutely certain; inevitable."

    Their journey began—with doubts, with fears—but also with ‘hope’.
    Under the starry sky — „the world“ whispered promises?

    John thought: “We'll succeed!”
    She whispered back: ‘Yes... we will.’
    Then, silence... and a smile.
        """

    @pytest.mark.asyncio
    async def test_process_text_to_chapters(self, text: str) -> None:
        words = await process_text_to_chapters(text)
        assert isinstance(words, list)
        assert all(isinstance(w, ChapterContentWordType) for w in words)
        for word in words:
            assert word.base
            assert word.origin
            assert not re.search(r"[„“!?‘—\-]", word.base)

    @pytest.mark.asyncio
    async def test_create_words(self, text: str) -> None:
        words = await process_text_to_chapters(text)
        chapter_entity = (await self._service.list())[0]
        word_chapter_service = WordChapterSaverService(self.init_repository_type)
        await word_chapter_service.save_words_from_chapter_content(
            chapter=chapter_entity, content=words
        )
        saved_words_indexes = await word_chapter_service.word_chapter_repo.get_by_chapter(chapter_id=chapter_entity.id)
        assert len(saved_words_indexes) == len(words)
