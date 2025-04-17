from __future__ import annotations
from domain.language.entities import LanguageEntity
from domain.language.exceptions import LanguageException, LanguagePermissionDenied
from application.abstract.services.crud import BaseCRUDService
from application.language.dtos import LanguageDTO, LanguageListDTO
from domain.language.interfaces.repository import LanguageRepository


class LanguageService(BaseCRUDService[LanguageEntity]):
    entity_class = LanguageEntity
    list_dto = LanguageListDTO
    item_dto = LanguageDTO
    not_found_exception = LanguageException
    entity_repository_type = LanguageRepository
    entity_permission_denied_exception = LanguagePermissionDenied

    def _set_acces_control_validators(self):
        ...
