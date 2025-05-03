from __future__ import annotations

from pydantic import Field
from application.abstract.dtos import BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemDTO, BaseItemsListDTO, \
    BaseActionResultDTO


class CreateChapterDTO(BaseCreateItemDTO):
    """
    DTO used to create a new chapter within a book.
    """
    name: str = Field(..., description="Title of the chapter.")
    book_id: int = Field(..., description="ID of the book to which this chapter belongs.")
    account_id: int | None = Field(default=None, description="ID of the user who created the chapter.")
    source_url: str | None = Field(default=None,
                                   description="URL or source reference from which the chapter originates.")


class CreateChapterWithTextDTO(CreateChapterDTO):
    text: str = Field(..., description="Chapter text.")


class CreateChapterResultDTO(BaseActionResultDTO):
    chapter_id: int


class ChapterDTO(BaseItemDTO):
    """
    DTO representing a complete view of a Chapter entity.
    """
    id: int = Field(..., description="Unique identifier of the chapter.")
    name: str = Field(..., description="Title of the chapter.")
    book_id: int = Field(..., description="ID of the book to which this chapter belongs.")
    account_id: int = Field(..., description="ID of the user who created the chapter.")
    source_url: str = Field(..., description="URL or source reference from which the chapter originates.")
    position: int = Field(..., description="Position of the chapter within the book.")
    is_ready: bool = Field(..., description="Flag indicating whether the chapter has been processed.")


class ChapterListDTO(BaseItemsListDTO):
    """
    DTO used to represent chapter summaries in list views.
    """
    id: int = Field(..., description="Unique identifier of the chapter.")
    name: str = Field(..., description="Title of the chapter.")
    position: int = Field(..., description="Position of the chapter within the book.")
    is_ready: bool = Field(..., description="Flag indicating whether the chapter has been processed.")


class UpdateChapterDTO(BaseUpdateItemDTO):
    """
    DTO used to update the details of an existing chapter.
    """
    name: str | None = Field(None, description="New or updated title of the chapter.")
    source_url: str | None = Field(None, description="New or updated source URL of the chapter.")
    position: int = Field(..., description="Position of the chapter within the book.")
