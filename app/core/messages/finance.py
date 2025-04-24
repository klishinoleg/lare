from __future__ import annotations

from decimal import Decimal

from domain.abstract import BaseEntity


class GetFinanceMessages[E: BaseEntity]:
    """
    Messages for finance operations
    """

    @staticmethod
    def payment_title() -> str:
        return "Purchase Credits"

    @staticmethod
    def payment_description() -> str:
        return "Purchase Credits to Use AI in the App."

    @staticmethod
    def credits_amount(credits_amount: Decimal) -> str:
        return "Credits: {} 💰".format(credits_amount)
