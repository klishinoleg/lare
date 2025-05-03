from __future__ import annotations

from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel, Field

from application.abstract.dtos import BaseModelWithSafeFields
from application.account.dtos import AccountDTO
from domain.auth_profile.enums import AuthProviderType


class AuthProfileDTO(BaseModelWithSafeFields):
    id: int = Field(..., description="Authotization profile ID")
    provider_type: AuthProviderType = Field(..., description="Authorization Provider Type")
    provider_id: str = Field(..., description="Authorization Provider internal ID")
    language_code: str | None = Field(None, description="Authorization profile Language Code")
    created_at: datetime = Field(..., description="Authorization profile Creation Date")


class AuthInitDataDTO[BM: BaseModel](BaseModel):
    """
    DTO for incoming authentication request from a third-party provider.

    This object contains data passed from a client (e.g., Telegram WebApp)
    and is used to create or validate an auth profile.

    Fields:
        provider_type: The enum value of the provider (e.g., TELEGRAM).
        provider_data: Dictionary with raw data needed for validation.
    """
    provider_type: AuthProviderType = Field(..., description="Type of the auth provider (e.g., TELEGRAM)")
    provider_data: BM = Field(..., description="Raw provider-specific authentication data")


class AuthResponseDTO(BaseModel):
    """
    DTO returned after successful authentication.

    Contains access token and user account info.

    Fields:
        token: JWT or other authentication token.
        account: Public representation of the authenticated user.
    """
    token: str = Field(..., description="Access token")
    account: AccountDTO = Field(..., description="Authenticated user account")


AUIDDTO = TypeVar("AUIDDTO", bound=AuthInitDataDTO)
