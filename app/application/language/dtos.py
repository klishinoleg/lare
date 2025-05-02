from pydantic import Field
from application.abstract.dtos import (
    BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemsListDTO, BaseItemDTO
)


class LanguageCreateDTO(BaseCreateItemDTO):
    name: str = Field(..., description="Display name of the language (e.g., English)")
    slug: str = Field(..., description="URL-friendly identifier (e.g., 'en')")
    code: str = Field(..., description="Language code (e.g., 'en', 'ru')")
    original_name: str = Field(..., description="Native name of the language (e.g., 'English', 'Русский')")
    ordering: int = Field(100, description="Custom ordering index for sorting")


class LanguageUpdateDTO(BaseUpdateItemDTO):
    name: str = Field(..., description="Display name of the language")
    slug: str = Field(..., description="URL-friendly identifier")
    code: str = Field(..., description="Language code")
    original_name: str = Field(..., description="Native name of the language")
    ordering: int = Field(100, description="Sorting index")


class LanguageListDTO(BaseItemsListDTO):
    name: str = Field(..., description="Display name of the language")
    slug: str = Field(..., description="URL-friendly identifier")
    code: str = Field(..., description="Language code")


class LanguageDTO(BaseItemDTO):
    name: str = Field(..., description="Display name of the language")
    slug: str = Field(..., description="URL-friendly identifier")
    code: str = Field(..., description="Language code")
    original_name: str = Field(..., description="Native name of the language")
    ordering: int = Field(..., description="Sorting index")
