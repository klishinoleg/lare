from pydantic import BaseModel, Field
from typing import Optional

from application.auth.dtos import AuthInitDataDTO


class WebAppUserDTO(BaseModel):
    id: int = Field(..., description="Unique identifier for the user or bot (up to 52 bits)")
    is_bot: Optional[bool] = Field(None, description="True if this user is a bot (receiver only)")
    first_name: str = Field(..., description="First name of the user or bot")
    last_name: Optional[str] = Field(None, description="Last name of the user or bot")
    username: Optional[str] = Field(None, description="Username of the user or bot")
    language_code: Optional[str] = Field(None, description="IETF language tag of the user's language")
    is_premium: Optional[bool] = Field(None, description="True if Telegram Premium user")
    added_to_attachment_menu: Optional[bool] = Field(None, description="True if user added bot to attachment menu")
    allows_write_to_pm: Optional[bool] = Field(None, description="True if user allowed bot to message them")
    photo_url: Optional[str] = Field(None, description="User’s profile photo URL (.jpeg or .svg)")


class WebAppChatDTO(BaseModel):
    id: int = Field(..., description="Unique identifier for the chat (up to 52 bits)")
    type: str = Field(..., description="Type of chat: group, supergroup, or channel")
    title: str = Field(..., description="Title of the chat")
    username: Optional[str] = Field(None, description="Chat username (optional)")
    photo_url: Optional[str] = Field(None, description="Chat photo URL (.jpeg or .svg)")


class TelegramWebAppInitDTO(BaseModel):
    query_id: Optional[str] = Field(None, description="Unique identifier for the Mini App session")
    user: WebAppUserDTO = Field(..., description="Current Telegram user")
    receiver: Optional[WebAppUserDTO] = Field(None, description="Chat partner of current user (attachment menu only)")
    chat: Optional[WebAppChatDTO] = Field(None, description="Chat where the bot was launched (attachment menu only)")
    chat_type: Optional[str] = Field(None, description="Type of chat from which the Mini App was opened")
    chat_instance: Optional[str] = Field(None, description="Global identifier of the chat")
    start_param: Optional[str] = Field(None, description="startattach parameter from the link")
    can_send_after: Optional[int] = Field(None, description="Seconds until bot can send message via answerWebAppQuery")
    auth_date: str = Field(..., description="Unix timestamp when the form was opened")
    hash: str = Field(..., description="HMAC-SHA-256 hash to validate data")
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
