from fastapi import APIRouter, Depends
from starlette import status
from application.book.services.chapter_crud_service import ChapterService
from core.messages.actions import GetActMessages
from domain.account.entities import AccountEntity
from domain.book.entities import ChapterEntity, BookEntity
from interfaces.fast_api.deps.account import get_current_account
from application.book.dtos.chapter import CreateChapterResultDTO, CreateChapterDTO, CreateChapterWithTextDTO, \
    ChapterListDTO
from application.book.services.book_crud_service import BookService
from application.book.dtos.book import (
    CreateBookDTO,
    UpdateBookDTO,
    BookDTO,
    BookListDTO
)
from interfaces.fast_api.routers.abstract.crud import BaseCRUDApiViewSet

router = APIRouter(prefix="/book", tags=["Books"])


class BookViewSet(BaseCRUDApiViewSet):
    schema = BookDTO
    list_schema = BookListDTO
    create_schema = CreateBookDTO
    update_schema = UpdateBookDTO
    service_type = BookService
    have_to_add_account_id_to_create_data = True
    update_auth = True
    post_auth = True
    get_auth = True

    @staticmethod
    @router.post("/create_chapter/", response_model=CreateChapterResultDTO, status_code=status.HTTP_201_CREATED)
    async def create_chapter(data: CreateChapterWithTextDTO,
                             account: AccountEntity = Depends(get_current_account)) -> CreateChapterResultDTO:
        chapter_service = ChapterService()
        data.account_id = account.id
        chapter_dto = CreateChapterDTO.create_from_dict(data.model_dump())
        entity = ChapterEntity(**chapter_dto.model_dump())
        chapter = await chapter_service.create_with_text(entity, data.text)
        return CreateChapterResultDTO(success=True,
                                      message=GetActMessages.chapter_created_await_parsing_content(chapter.name),
                                      chapter_id=chapter.id
                                      )

    @staticmethod
    @router.get("/{bookd_id}/chapters/", response_model=list[ChapterListDTO], status_code=status.HTTP_200_OK)
    async def get_chapters(
            bookd_id: int,
            account: AccountEntity = Depends(get_current_account)) -> list[ChapterListDTO]:
        chapter_service = ChapterService()
        chapters = await chapter_service.repository.get_by_book(book_id=bookd_id, account_id=account.id)
        return [ChapterListDTO.model_validate(ch.to_dict()) for ch in chapters]

    async def _get_list(self, account: AccountEntity) -> list[BookEntity]:
        book_service = BookService()
        return await book_service.repository.get_by_account(account_id=account.id)


view = BookViewSet(router)
