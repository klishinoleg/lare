from fastapi import APIRouter
from starlette import status

from application.language.service import LanguageService
from application.language.dtos import (
    LanguageDTO,
    LanguageListDTO,
    LanguageCreateDTO,
    LanguageUpdateDTO
)
from domain.language.entities import LanguageEntity
from interfaces.fast_api.routers.abstract.crud import BaseCRUDApiViewSet

router = APIRouter(prefix="/language", tags=["Languages"])


class LanguageViewSet(
    BaseCRUDApiViewSet[
        LanguageService, LanguageEntity, LanguageDTO, LanguageListDTO, LanguageCreateDTO, LanguageUpdateDTO
    ]
):
    schema = LanguageDTO
    list_schema = LanguageListDTO
    create_schema = LanguageCreateDTO
    update_schema = LanguageUpdateDTO
    service_type = LanguageService
    create_denied = True
    update_denied = True


view = LanguageViewSet(router)


@view.router.get("/init/", response_model=list[LanguageListDTO], status_code=status.HTTP_200_OK)
async def list_or_init() -> list[LanguageListDTO]:
    return [
        LanguageListDTO.model_validate(language.to_dict()) for language in await view.get_service().get_or_init()
    ]


view.set_routes()
