from __future__ import annotations
from decimal import Decimal
from domain.abstract import BaseEntity
from domain.account.entities import AccountEntity
from core.i18n import _


class GetBotMessages[E: BaseEntity]:
    """
    Messages for finance operations
    """

    @staticmethod
    def start_for_new(account: AccountEntity) -> str:
        return "\n".join([
            _("*👋 Hello, {}!* Welcome to *Lazy Reader*").format(account.public_name or account.username),
            _("– your ultimate tool for reading, translation, and language learning! 📖✨"),
            "",
            _("📚 *What can you do with Lazy Reader?*"),
            _("🔹 *Create your own books* and add articles to them 📜"),
            _("🔹 *Automatically fetch subtitles* from popular websites 🎬"),
            _("🔹 *Translate and listen to text* in multiple languages 🌍🔊"),
            _("🔹 *Break down text into phrases and words* for easy learning 🔠"),
            _("🔹 *Learn new words and phrases* with the Telegram bot 🤖"),
            _("🔹 *Analyze word etymology* and discover their origins 🔍"),
            _("🔹 *Discuss language rules* and ask AI for explanations 🤖💡"),
            "",
            _("🎉 *Ready to start?* Click the button below and explore a new world of learning!")
        ])

    @staticmethod
    def start_for_exist(account: AccountEntity) -> str:
        return "\n".join([
            _("Hello, {}!").format(account.public_name or account.username),
            _("Thank you for using <b>Lazy Reader</b>."),
            _("We’re here to help you improve your reading and language skills! 🚀")
        ])

    @staticmethod
    def open_webapp() -> str:
        return _("🚀 Open the App")

    @staticmethod
    def add_credits_start_bonus(credits_amount: Decimal) -> str:
        return _("Start bonus credits have been added to your account: {}★".format(credits_amount))

    @staticmethod
    def start_bonus_already_sended() -> str:
        return _("You have already sent a start bonus.")

    @staticmethod
    def start_bonus_requested() -> str:
        return _("You have requested a start bonus.")

    @staticmethod
    def add_credits_bill(credits_amount: Decimal) -> str:
        return _("Bill successful, credits have been added to your account: {}★".format(credits_amount))

    @staticmethod
    def confirm_manual_bill(account: AccountEntity) -> str:
        return _("Confirm add credits for {account.public_name} {account.username}").format(account=account)
