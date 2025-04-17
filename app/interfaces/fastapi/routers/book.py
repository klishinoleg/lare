from fastapi import APIRouter
from application.book.services.book_crud_service import BookService
from application.book.dtos.book import (
    CreateBookDTO,
    UpdateBookDTO,
    BookDTO,
    BookListDTO
)
from interfaces.fastapi.routers.abstract.crud import BaseCRUDApiViewSet

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


view = BookViewSet(router)
