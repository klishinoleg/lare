from __future__ import annotations
from domain.language.entities import LanguageEntity
from domain.language.exceptions import LanguageException, LanguagePermissionDenied
from application.abstract.services.crud import BaseCRUDService
from application.language.dtos import LanguageDTO, LanguageListDTO, LanguageCreateDTO, LanguageUpdateDTO
from domain.language.interfaces.repository import LanguageRepository
from infrastructure.loaders.load_languages import load_languages_init_entities


class LanguageService(
    BaseCRUDService[
        LanguageEntity, LanguageRepository, LanguageDTO,
        LanguageListDTO, LanguageCreateDTO, LanguageUpdateDTO]
):
    entity_class = LanguageEntity
    list_dto = LanguageListDTO
    item_dto = LanguageDTO
    not_found_exception = LanguageException
    entity_repository_type = LanguageRepository
    entity_permission_denied_exception = LanguagePermissionDenied

    def _set_acces_control_validators(self) -> None:
        ...

    async def get_or_init(self) -> list[LanguageEntity]:
        languages = await self.list()
        if len(languages) == 0:
            languages_entities = load_languages_init_entities(without_id=True)
            for language in languages_entities:
                await self.create(language)
        return await self.list()
