from core.di.bot import DIBot
from domain.auth_profile.enums import AuthProviderType
from interfaces.bot.telegram import TelegramBot


def register_bots() -> None:
    DIBot.register(TelegramBot, AuthProviderType.TELEGRAM)
