from __future__ import annotations
from application.access_control.validators import OwnedByAccountValidator
from application.access_control.services import Accessor
from domain.book.entities import BookEntity
from domain.book.exceptions import BookNotFoundError, BookPermissionDenied
from application.abstract.services.crud import BaseCRUDService
from application.book.dtos.book import BookDTO, BookListDTO, CreateBookDTO, UpdateBookDTO
from domain.book.interfaces.repository import BookRepository


class BookService(BaseCRUDService[BookEntity, BookRepository, BookDTO, BookListDTO, CreateBookDTO, UpdateBookDTO]):
    entity_class = BookEntity
    list_dto = BookListDTO
    item_dto = BookDTO
    not_found_exception = BookNotFoundError
    entity_repository_type = BookRepository
    entity_permission_denied_exception = BookPermissionDenied

    def _set_acces_control_validators(self) -> None:
        Accessor.register(self.entity_class, OwnedByAccountValidator(), self.entity_permission_denied_exception)
