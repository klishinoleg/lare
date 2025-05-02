from __future__ import annotations
from core.i18n import _
from domain.abstract import BaseEntity
from domain.account.entities import AccountEntity
from domain.auth_profile.enums import AuthProviderType


class GetExMessages[E: BaseEntity]:
    """
    A centralized helper for formatting common domain exception messages.

    This class provides reusable static methods for generating human-readable
    error messages used in validation or domain-level exceptions. Helps maintain
    consistency across exception texts throughout the application.
    """

    @staticmethod
    def username_already_exists(username: str = "") -> str:
        return _("Username {} already exists").format(username)

    @staticmethod
    def auth_profile_invalid_data(additional_info: str = "") -> str:
        return _("Invalid auth profile data: {}").format(additional_info)

    @staticmethod
    def auth_provider_not_registered(provider_type: AuthProviderType) -> str:
        return _("No auth provider registered for: {}").format(provider_type.value)

    @staticmethod
    def invalid_token() -> str:
        return _("Invalid token")

    @staticmethod
    def account_not_found(info: str | int = "") -> str:
        return _("Account not found {}").format(str(info)).strip()

    @staticmethod
    def telegram_invalid_hash() -> str:
        return _("Invalid Telegram hash")

    @staticmethod
    def telegram_auth_expired() -> str:
        return _("Telegram auth expired")

    @staticmethod
    def password_auth_profile_not_found() -> str:
        return _("Password profile not found")

    @staticmethod
    def invalid_username_or_password() -> str:
        return _("Invalid username or password")

    @staticmethod
    def permision_denied(entity: E, account: AccountEntity) -> str:
        return _("Access denied for {} by {}").format(type(entity).__name__, account.username)

    @staticmethod
    def wrong_repeat_password() -> str:
        return _("Wrong repeat password")

    @staticmethod
    def for_make_payment_you_have_to_create_auth_profile(auth_provider_type: AuthProviderType) -> str:
        return _("For make payment you have to create auth profile: {}").format(auth_provider_type.value)

    @staticmethod
    def event_streaming_timeout(key: str | None, timeout: float) -> str:
        return _("Event streaming timeout for key {}: {} seconds").format(key, timeout)
