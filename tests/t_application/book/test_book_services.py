from __future__ import annotations
from random import shuffle
import pytest
from application.book.services.book_crud_service import BookService
from application.language.service import LanguageService
from core.enums.repository.types import RepositoryTypes
from domain.book.entities import BookEntity
from domain.book.interfaces.repository import BookRepository
from infrastructure.loaders.load_languages import load_languages_init_entities
from tests.t_application.abstract.base_test_crud import BaseCRUDServiceTest
from tests.t_domain.entities.book import BookFactory


class TestBookService(BaseCRUDServiceTest[BookEntity, BookRepository, BookService, BookFactory]):
    init_service_type = BookService
    init_entity_repository = BookRepository
    factory = BookFactory
    _account = None
    _is_languages_ready = False
    _language_service: LanguageService | None = None

    def _get_language_service(self) -> LanguageService:
        if not self._language_service:
            self._language_service = LanguageService(RepositoryTypes.MOCK)
        return self._language_service

    @pytest.fixture(autouse=True)
    async def create_languages(self) -> None:
        if not self._is_languages_ready:
            languages_entities = load_languages_init_entities()
            language_service = self._get_language_service()
            for language in languages_entities:
                await language_service.create(language)
            self._is_languages_ready = True

    async def _get_fake_entity(self, **kwargs: dict) -> BookEntity:
        language_service = self._get_language_service()
        languages = await language_service.list()
        shuffle(languages)
        language_id = languages[0].id
        main_account = await self._get_main_account()
        return await super()._get_fake_entity(
            account_id=main_account.id, language_id=language_id)  # type: ignore[arg-type]
