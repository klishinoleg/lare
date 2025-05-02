from __future__ import annotations
from core.i18n import _
from decimal import Decimal
from domain.abstract import BaseEntity


class GetFinanceMessages[E: BaseEntity]:
    """
    Messages for finance operations
    """

    @staticmethod
    def payment_title() -> str:
        return _("Purchase Credits")

    @staticmethod
    def payment_description() -> str:
        return _("Purchase Credits to Use AI in the App.")

    @staticmethod
    def credits_amount(credits_amount: Decimal) -> str:
        return _("Credits: {} 💰").format(credits_amount)

    @staticmethod
    def start_bonus_exist() -> str:
        return _("You already have a start bonus")

    @staticmethod
    def bill_has_been_confirmed() -> str:
        return _("Bill has been confirmed successfully.")

    @staticmethod
    def bill_has_been_removed() -> str:
        return _("Bill has been deleted.")

    @staticmethod
    def manual_bill_message_format() -> str:
        return _("Format should be: credits:account_id:credits_amount:cost:RUB")

    @staticmethod
    def incorrect_credits_or_cost_format() -> str:
        return _("Incorrect credits or cost format")
