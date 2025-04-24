from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from domain.abstract import BaseEntity
from domain.mixins.timestamp_mixin import TimestampMixin
from domain.mixins.with_active_mixin import WithActiveMixin


@dataclass(slots=True, kw_only=True)
class AccountEntity(BaseEntity, WithActiveMixin, TimestampMixin):
    """
    Domain entity representing a user account.

    This entity contains core user data such as username, email, and balance (credits).
    It is a pure domain object that encapsulates only business-related logic and state.

    Inherits:
        BaseEntity: Provides an `id` field and entity utility methods.
        WithActiveMixin: Adds `is_active` flag for soft deletion or suspension.
        TimestampMixin: Adds `created_at` and `updated_at` timestamps.

    Attributes:
        username (str): Unique username for the account.
        public_name (str | None): Display name shown to other users.
        email (str | None): Email address (hidden in repr).
        credits (float): Balance of credits associated with the account.

    Methods:
        has_enough_credits(amount: float | None = None) -> bool:
            Checks if the account has sufficient credits.
            If `amount` is None, returns True if `credits > 0`.
            Otherwise, returns True if `credits >= amount`.
    """

    username: str
    public_name: str | None
    email: str | None = field(repr=False)
    credits: Decimal = field(repr=False, default_factory=Decimal)

    def has_enough_credits(self, amount: Decimal | None = None) -> bool:
        """
        Check if the user has enough credits.

        Args:
            amount (Decimal | None): Optional amount to check against.

        Returns:
            bool: True if credits are sufficient, False otherwise.
        """
        if amount is None:
            return self.credits > 0
        return self.credits >= amount
