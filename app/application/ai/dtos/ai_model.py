from decimal import Decimal
from pydantic import Field
from application.abstract.dtos import BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemDTO, BaseItemsListDTO


class CreateAiModelDTO(BaseCreateItemDTO):
    """
    DTO for creating a new AI model.
    """
    name: str = Field(..., description="Display name of the AI model.")
    model: str = Field(..., description="Technical ID used in provider calls.")
    input_cost: Decimal = Field(..., description="Cost per 1000 input tokens.")
    output_cost: Decimal | None = Field(None, description="Cost per 1000 output tokens (optional).")
    kef: int = Field(1, description="Cost multiplier (default is 1).")
    allow_to: list[str] = Field(default_factory=list, description="Allowed usage types (as strings).")


class UpdateAiModelDTO(BaseUpdateItemDTO):
    """
    DTO for updating an existing AI model.
    """
    name: str | None = Field(None, description="Updated display name.")
    model: str | None = Field(None, description="Updated technical ID.")
    input_cost: Decimal | None = Field(None, description="Updated input token cost.")
    output_cost: Decimal | None = Field(None, description="Updated output token cost.")
    kef: int | None = Field(None, description="Updated multiplier.")
    allow_to: list[str] | None = Field(None, description="Updated list of allowed usage types.")
    is_active: bool | None = Field(None, description="Model availability flag.")


class AiModelDTO(BaseItemDTO):
    """
    Full DTO for reading AI model data.
    """
    id: int = Field(..., description="ID of the AI model.")
    name: str = Field(..., description="Display name of the model.")
    model: str = Field(..., description="Technical ID used in integration.")
    input_cost: Decimal = Field(..., description="Cost per 1000 input tokens.")
    output_cost: Decimal | None = Field(None, description="Cost per 1000 output tokens.")
    kef: int = Field(..., description="Cost multiplier.")
    allow_to: list[str] = Field(..., description="Allowed usage types.")
    is_active: bool = Field(..., description="Whether the model is active.")


class AiModelListDTO(BaseItemsListDTO):
    """
    Lightweight DTO for listing AI models.
    """
    id: int = Field(..., description="Model ID.")
    name: str = Field(..., description="Model name.")
    model: str = Field(..., description="Model technical ID.")
    is_active: bool = Field(..., description="Model enabled or not.")
