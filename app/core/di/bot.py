from typing import Type
from core.config import settings
from core.di.repository import DIRepository
from core.enums.bot.bot_types import BotTypes
from domain.account.entities import AccountEntity
from domain.auth_profile.enums import AuthProviderType
from domain.auth_profile.interfaces.repository import AuthProfileRepository
from interfaces.bot.base_bot_interface import BaseBotInterface


class BotInfo[BBI: BaseBotInterface]:
    bot: Type[BBI]
    auth_provider: Type[AuthProviderType]

    def __init__(self, bot: Type[BBI], auth_provider: AuthProviderType):
        self.bot: Type[BBI] = bot
        self.auth_provider: AuthProviderType = auth_provider


class DIBot[BBI: BaseBotInterface]:
    _bot_types: dict[BotTypes, BotInfo] = {}

    @classmethod
    async def get(cls, account_entity: AccountEntity, bot_type: BotTypes | None = None) -> BBI:
        if not bot_type:
            bot_type = settings.default_bot
        bot_info = cls._bot_types.get(bot_type)
        if not bot_info:
            raise NotImplementedError(f"Bot type {bot_type} not register")
        auth_profile_repository: AuthProfileRepository = DIRepository[AuthProfileRepository].get_repository(
            AuthProfileRepository)()
        auth_profile = await auth_profile_repository.get_by_account_id(account_id=account_entity.id,
                                                                       provider_type=bot_info.auth_provider)
        return await bot_info.bot.get_with_auth_provider(account=account_entity, auth_profile=auth_profile)

    @classmethod
    async def get_bot_model(cls, bot_type: BotTypes | None = None) -> Type[BBI]:
        bot_info = cls._bot_types.get(bot_type)
        if not bot_info:
            raise NotImplementedError(f"Bot type {bot_type} not register")
        return bot_info.bot

    @classmethod
    def register(cls, bot: Type[BBI], auth_provider: AuthProviderType) -> None:
        cls._bot_types[bot.bot_type] = BotInfo(bot=bot, auth_provider=auth_provider)
