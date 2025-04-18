from __future__ import annotations
from application.book.services.chapter_crud_service import ChapterService
from domain.book.entities import ChapterEntity
from domain.book.interfaces.repository import ChapterRepository
from tests.t_application.abstract.base_test_crud import BaseCRUDServiceTest
from tests.t_domain.entities.chapter import ChapterFactory


class TestChapterService(BaseCRUDServiceTest[ChapterEntity, ChapterRepository, ChapterService, ChapterFactory]):
    init_service_type = ChapterService
    init_entity_repository = ChapterRepository
    factory = ChapterFactory
    _account = None

    async def _get_fake_entity(self, **kwargs: dict) -> ChapterEntity:
        main_account = await self._get_main_account()
        return await super()._get_fake_entity(account_id=main_account.id, book_id=1)  # type: ignore[arg-type]
