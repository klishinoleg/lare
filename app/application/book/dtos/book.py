from __future__ import annotations

from pydantic import Field
from application.abstract.dtos import BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemDTO, BaseItemsListDTO


class CreateBookDTO(BaseCreateItemDTO):
    """
    DTO used to create a new Book.
    """
    name: str = Field(..., description="The title of the book.")
    language_id: int = Field(..., description="The ID of the language the book is written in.")
    account_id: int | None = Field(None, description="The ID of the account creating the book.")
    image: str = Field(..., description="Image base64")


class BookDTO(BaseItemDTO):
    """
    DTO representing a complete view of a Book entity.
    """
    id: int = Field(..., description="Unique identifier of the book.")
    name: str = Field(..., description="The title of the book.")
    language_id: int = Field(..., description="The ID of the language the book is written in.")
    account_id: int = Field(..., description="The ID of the user who created the book.")
    image: str = Field(..., description="Image url")
    chapters_cnt: int = Field(..., description="The number of chapters of the book.")


class BookListDTO(BaseItemsListDTO):
    """
    DTO representing a lightweight summary of a Book used in listings.
    """
    id: int = Field(..., description="Unique identifier of the book.")
    name: str = Field(..., description="The title of the book.")
    image: str | None = Field(default=None, description="Image url")
    chapters_cnt: int = Field(..., description="The number of chapters of the book.")


class UpdateBookDTO(BaseUpdateItemDTO):
    """
    DTO used to update book information.
    """
    name: str | None = Field(None, description="The updated title of the book, if changed.")
    image: str = Field(..., description="Image base64")
