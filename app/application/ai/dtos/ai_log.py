from pydantic import Field
from application.abstract.dtos import BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemDTO, BaseItemsListDTO


class CreateAiLogDTO(BaseCreateItemDTO):
    """
    DTO for creating a new AI log entry.
    """
    ai_request: str = Field(..., description="Prompt sent to the AI provider.")
    ai_response: str = Field(..., description="Text or result returned by AI.")
    ai_type: str = Field(..., description="Type of AI provider (e.g. 'gpt', 'google').")
    ai_model_id: int = Field(..., description="ID of the AI model used.")
    file_path: str | None = Field(None, description="Path to file if AI returned a media file.")
    source_language: int = Field(..., description="ID of the source language.")
    target_language: int | None = Field(None, description="ID of the target language (optional).")
    usage_type: str = Field(..., description="Type of usage (e.g., 'TRANSLATE', 'VOICE').")
    account_id: int = Field(..., description="ID of the account who initiated the request.")
    hash_str: str = Field(..., description="Hash of request used for caching and deduplication.")


class UpdateAiLogDTO(BaseUpdateItemDTO):
    """
    DTO for updating AI logs (admin or correction use).
    """
    ai_response: str | None = Field(None, description="Corrected response (if needed).")
    file_path: str | None = Field(None, description="Corrected or updated file path.")


class AiLogDTO(BaseItemDTO):
    """
    Full DTO for viewing an AI log entry.
    """
    id: int = Field(..., description="Log ID.")
    ai_request: str = Field(..., description="Original request prompt.")
    ai_response: str = Field(..., description="Returned AI output.")
    ai_type: str = Field(..., description="AI provider type.")
    ai_model_id: int = Field(..., description="ID of the used AI model.")
    file_path: str | None = Field(None, description="Audio file path if applicable.")
    source_language: int = Field(..., description="Source language ID.")
    target_language: int | None = Field(None, description="Target language ID.")
    usage_type: str = Field(..., description="Context of AI usage.")
    account_id: int = Field(..., description="Requesting account ID.")
    hash_str: str = Field(..., description="Hash used to prevent duplication.")


class AiLogListDTO(BaseItemsListDTO):
    """
    DTO for displaying a short list of AI logs.
    """
    id: int = Field(..., description="Log ID.")
    ai_type: str = Field(..., description="AI provider type.")
    usage_type: str = Field(..., description="Usage context (e.g., 'TRANSLATE').")
    hash_str: str = Field(..., description="Request hash.")
