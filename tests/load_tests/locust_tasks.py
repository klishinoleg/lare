from time import sleep
from locust import HttpUser, task, between
from application.account.dtos import AccountDTO
from application.auth.dtos import AuthResponseDTO
from application.book.dtos.book import BookListDTO, CreateBookDTO
from application.book.dtos.chapter import CreateChapterWithTextDTO, CreateChapterResultDTO, ChapterListDTO
from application.language.dtos import LanguageListDTO
from domain.book.entities import BookEntity
from tests.t_infrastructure.auth.factory.telegram import create_fake_telegram_provider_data
from tests.t_domain.entities.book import BookFactory
from tests.t_domain.entities.chapter import ChapterWithTextFactory
import logging


class LazyReaderTestUser(HttpUser):
    token: str
    account: AccountDTO
    books: list[BookListDTO] = []
    languages: list[LanguageListDTO] = []
    headers: dict[str, str]
    wait_time = between(1, 3)

    def on_start(self) -> None:
        self._auth_telegram()
        languages_response = self.client.get("/language/init/")
        assert languages_response.status_code == 200
        languages = languages_response.json()
        self.languages = [LanguageListDTO.model_validate(language) for language in languages]

    def _auth_telegram(self) -> None:
        fake_data = create_fake_telegram_provider_data()
        response = self.client.post("/auth/telegram/", json=fake_data.model_dump())
        assert response.status_code == 200
        data = response.json()
        data_dto = AuthResponseDTO.model_validate(data)
        self.account = data_dto.account
        self.token = data_dto.token
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task
    def create_book(self) -> None:
        language = next(language for language in self.languages if language.name == "English")
        if not language:
            assert False, "No English language found"
        book: BookEntity = BookFactory(account_id=self.account.id, language_id=language.id)
        create_book_dto = CreateBookDTO.model_validate(book.to_dict())
        response = self.client.post("/book/", json=create_book_dto.model_dump(), headers=self.headers)
        assert response.status_code == 201

    @task
    def list_books(self) -> None:
        response = self.client.get("/book/", headers=self.headers)
        assert response.status_code == 200
        self.books = [BookListDTO.model_validate(b) for b in response.json()]

    @task
    def create_chapter(self) -> None:
        from time import monotonic
        self.list_books()
        if len(self.books) == 0:
            self.create_book()
            self.list_books()
        book = self.books[0]
        create_chapter_dto: CreateChapterWithTextDTO = ChapterWithTextFactory(
            book_id=book.id, account_id=self.account.id
        )
        response = self.client.post("/book/create_chapter/", json=create_chapter_dto.model_dump(), headers=self.headers)
        assert response.status_code == 201
        create_chapter_response_dto = CreateChapterResultDTO.model_validate(response.json())
        assert create_chapter_response_dto.success

        start = monotonic()
        is_ready = False
        for i in range(1, 250):
            sleep(1 / 10)
            chapter_response = self.client.get(f"/book/{book.id}/chapters/", headers=self.headers)
            assert chapter_response.status_code == 200
            chapters_dto = [ChapterListDTO.model_validate(ch) for ch in chapter_response.json()]
            chapter = next((ch for ch in chapters_dto if ch.id == create_chapter_response_dto.chapter_id), None)
            is_ready = chapter is not None and chapter.is_ready
            if is_ready:
                break
        duration = monotonic() - start
        logging.info(
            f"⏱ Chapter {create_chapter_response_dto.chapter_id} ready in {duration:.2f} seconds "
            f"/ {self.account.username} / {book.id} : {book.name}")
        # Report to Locust metrics
        self.environment.events.request.fire(
            request_type="GET",
            name="chapter_ready_polling",
            response_time=duration * 1000,
            response_length=0,
            context={},
            exception=None if is_ready else Exception("Chapter not ready in time (25s)")
        )
        assert is_ready
