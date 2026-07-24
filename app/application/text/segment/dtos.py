from __future__ import annotations
from pydantic import Field, BaseModel
from application.abstract.dtos import BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemDTO, BaseItemsListDTO
from domain.text_data.enums import TextActionsTypes, TextTranslateTypes


class CreateSegmentDTO(BaseCreateItemDTO):
    """
    DTO used to create a new Segment.
    """
    name: str = Field(..., description="The text content of the segment.")
    language_id: int = Field(..., description="The ID of the language this segment is in.")


class SegmentDTO(BaseItemDTO):
    """
    DTO representing a full segment with metadata.
    """
    id: int = Field(..., description="Unique identifier of the segment.")
    name: str = Field(..., description="Text content of the segment.")
    language_id: int = Field(..., description="ID of the language of the segment.")


class SegmentListDTO(BaseItemsListDTO):
    """
    DTO representing a lightweight summary of a Segment.
    """
    id: int = Field(..., description="Unique identifier of the segment.")
    name: str = Field(..., description="Text content of the segment.")


class UpdateSegmentDTO(BaseUpdateItemDTO):
    """
    DTO used to update segment details.
    """
    name: str | None = Field(None, description="Updated text content of the segment.")
    language_id: int | None = Field(None, description="Updated language ID, if changed.")


class CreateSegmentByWordChapterIndexesDTO(BaseModel):
    """
    DTO used to create a new Segment by word chapter indexes.
    """
    indexes: list[int] = Field(..., description="Unique identifiers of the chapter indexes.")
    a: TextActionsTypes = Field(..., description="Action type after creation.")
    translate_type: TextTranslateTypes | None = Field(None, description="Translation type if it translate.")
