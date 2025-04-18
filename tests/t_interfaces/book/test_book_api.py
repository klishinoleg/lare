from random import shuffle

from starlette.testclient import TestClient
from domain.book.entities import BookEntity
from application.auth.dtos import AuthResponseDTO
from tests.t_domain.entities.book import BookFactory
from tests.t_interfaces.abstract.base_test_api_crud import BaseAPICRUDTest
from application.book.dtos.book import CreateBookDTO, UpdateBookDTO, BookDTO, BookListDTO


class TestBookAPI(BaseAPICRUDTest[BookEntity, BookFactory, BookDTO, BookListDTO, CreateBookDTO, UpdateBookDTO]):
    route = "/book"
    languages_route = "/language"
    factory = BookFactory
    init_create_dto = CreateBookDTO
    init_update_dto = UpdateBookDTO
    init_item_dto = BookDTO
    init_list_dto = BookListDTO

    def _from_factory(self, client: TestClient, auth_user_data: AuthResponseDTO, **kwargs: dict) -> BookEntity:
        languages: list = client.get(self.languages_route).json()
        if len(languages) == 0:
            self._create_languages(client, limit=10)
            languages = client.get(self.languages_route).json()
        shuffle(languages)
        return self.factory(account_id=auth_user_data.account.id, language_id=languages[0].get("id"))
