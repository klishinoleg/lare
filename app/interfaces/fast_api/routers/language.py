from fastapi import APIRouter
from application.language.service import LanguageService
from application.language.dtos import (
    LanguageDTO,
    LanguageListDTO,
    LanguageCreateDTO,
    LanguageUpdateDTO
)
from interfaces.fast_api.routers.abstract.crud import BaseCRUDApiViewSet

router = APIRouter(prefix="/language", tags=["Languages"])


class LanguageViewSet(BaseCRUDApiViewSet):
    schema = LanguageDTO
    list_schema = LanguageListDTO
    create_schema = LanguageCreateDTO
    update_schema = LanguageUpdateDTO
    service_type = LanguageService
    create_denied = True
    update_denied = True


view = LanguageViewSet(router)
