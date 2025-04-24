from random import shuffle
from time import sleep

import pytest

from application.book.dtos.chapter import CreateChapterWithTextDTO
from domain.book.entities import BookEntity
from application.auth.dtos import AuthResponseDTO
from tests.t_domain.entities.book import BookFactory
from tests.t_domain.entities.chapter import ChapterWithTextFactory
from tests.t_interfaces.abstract.base_test_api_crud import BaseAPICRUDTest
from application.book.dtos.book import CreateBookDTO, UpdateBookDTO, BookDTO, BookListDTO
from httpx import AsyncClient


class TestBookAPI(BaseAPICRUDTest[BookEntity, BookFactory, BookDTO, BookListDTO, CreateBookDTO, UpdateBookDTO]):
    route = "/book"
    languages_route = "/language/"
    factory = BookFactory
    init_create_dto = CreateBookDTO
    init_update_dto = UpdateBookDTO
    init_item_dto = BookDTO
    init_list_dto = BookListDTO

    async def _from_factory(self, client: AsyncClient, auth_user_data: AuthResponseDTO, **kwargs: dict) -> BookEntity:
        languages: list = (await client.get(self.languages_route)).json()
        if len(languages) == 0:
            await self._create_languages(client, limit=10)
            languages = (await client.get(self.languages_route)).json()
        shuffle(languages)
        return self.factory(account_id=auth_user_data.account.id, language_id=languages[0].get("id"))

    @pytest.mark.asyncio
    async def test_create_chapter_with_text(self, client: AsyncClient, auth_user_data: AuthResponseDTO) -> None:
        """
        Testing chapter events
        :param client:
        :param auth_user_data:
        :return:
        """
        _, response = await self._create_entity(client, auth_user_data)
        headers = self._get_auth_headers(auth_user_data)
        my_books_response = await client.get(self.route + "/", headers=headers)
        assert my_books_response.status_code == 200
        my_books = my_books_response.json()
        assert len(my_books) > 0
        book = my_books[0]
        chapter: CreateChapterWithTextDTO = ChapterWithTextFactory(book_id=book.get("id"))
        create_chapter_response = await client.post(
            self.route + "/create_chapter/",
            json=chapter.model_dump(),
            headers=headers
        )
        assert create_chapter_response.status_code == 201
        data = create_chapter_response.json()
        chapter_id = data.get("chapter_id")
        assert isinstance(data.get("chapter_id"), int)
        is_ready = False
        for i in range(5):
            sleep(1)
            chapters_response = await client.get(self.route + f"/{book.get("id")}/chapters/", headers=headers)
            assert chapters_response.status_code == 200
            chapters: list[dict] = chapters_response.json()
            assert len(chapters) > 0
            chapt = next((ch for ch in chapters if ch.get("id") == chapter_id), None)
            assert isinstance(chapt, dict)
            is_ready = chapt.get("is_ready", is_ready)
            if is_ready:
                break
        assert is_ready
