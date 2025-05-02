from aiogram.types import Chat, User
from pydantic import BaseModel, Field
from typing import Optional

from application.auth.dtos import AuthInitDataDTO


class TelegramWebAppInitDTO(BaseModel):
    user: User = Field(..., description="Current Telegram user")
    query_id: Optional[str] = Field(None, description="Unique identifier for the Mini App session")
    receiver: Optional[User] = Field(None, description="Chat partner of current user (attachment menu only)")
    chat: Optional[Chat] = Field(None, description="Chat where the bot was launched (attachment menu only)")
    chat_type: Optional[str] = Field(None, description="Type of chat from which the Mini App was opened")
    chat_instance: Optional[str] = Field(None, description="Global identifier of the chat")
    start_param: Optional[str] = Field(None, description="startattach parameter from the link")
    can_send_after: Optional[int] = Field(None, description="Seconds until bot can send message via answerWebAppQuery")
    auth_date: str | None = Field(None, description="Unix timestamp when the form was opened")
    hash: Optional[str] = Field(None, description="HMAC-SHA-256 hash to validate data")
    signature: Optional[str] = Field(None, description="Signature for third-party verification (excluding hash)")


class TelegramProviderDataDTO(BaseModel):
    init_data_unsafe: TelegramWebAppInitDTO = Field(
        ...,
        description="initDataUnsafe: An object with input data transferred to the Mini App.")
    init_data: str = Field(
        ...,
        description="initData: A string with raw data transferred to the Mini App, convenient for validating data.")


class TelegramAuthInitDataDTO(AuthInitDataDTO):
    provider_data: TelegramProviderDataDTO = Field(..., description="Telegram initDataUnsafe and initData")
