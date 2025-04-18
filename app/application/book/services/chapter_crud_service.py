from __future__ import annotations

from application.access_control.services import Accessor
from domain.book.entities import ChapterEntity
from domain.book.exceptions import ChapterNotFoundError, ChapterPermissionDenied
from application.abstract.services.crud import BaseCRUDService
from application.book.dtos.chapter import ChapterDTO, ChapterListDTO, CreateChapterDTO, UpdateChapterDTO
from domain.book.interfaces.repository import ChapterRepository
from application.access_control.validators.owned_by_account_validator import OwnedByAccountValidator


class ChapterService(
    BaseCRUDService[ChapterEntity, ChapterRepository, ChapterDTO, ChapterListDTO, CreateChapterDTO, UpdateChapterDTO]
):
    entity_class = ChapterEntity
    list_dto = ChapterListDTO
    item_dto = ChapterDTO
    not_found_exception = ChapterNotFoundError
    entity_repository_type = ChapterRepository
    entity_permission_denied_exception = ChapterPermissionDenied

    def _set_acces_control_validators(self) -> None:
        Accessor.register(ChapterEntity, OwnedByAccountValidator(), ChapterPermissionDenied)
