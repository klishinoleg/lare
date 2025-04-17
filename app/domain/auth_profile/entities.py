from __future__ import annotations

from dataclasses import dataclass

from domain.abstract import BaseEntity
from domain.auth_profile.enums import AuthProviderType
from domain.mixins.timestamp_mixin import TimestampMixin


@dataclass(slots=True, kw_only=True)
class AuthProfileEntity(TimestampMixin, BaseEntity):
    """
    Domain entity representing an external authentication profile.

    This entity links a user account to a third-party auth provider (e.g. Telegram).
    It stores the provider type, provider-specific user ID, and any raw data
    used to validate or reconstruct the login session.

    Inherits:
        BaseEntity: Adds an `id` field and utility methods.
        TimestampMixin: Adds `created_at` and `updated_at` timestamps.

    Attributes:
        account_id (int): ID of the user account this profile is linked to.
        provider_type (AuthProviderType): Type of auth provider (e.g. TELEGRAM).
        provider_id (str): Unique ID assigned by the auth provider (e.g. Telegram user ID).
        provider_data (dict): Raw provider-specific data used for authentication.
        language_code (str): ISO 639-1 language code of the auth provider.
    """
    account_id: int
    provider_type: AuthProviderType
    provider_id: str
    provider_data: dict
    language_code: str | None
