import asyncio
import re
from time import monotonic
from typing import AsyncGenerator
from httpx import AsyncClient
from application.account.dtos import AccountDTO
from application.auth.dtos import AuthResponseDTO
from core.config import settings
from core.messages.bot import GetBotMessages
from domain.account.entities import AccountEntity
from tests.t_infrastructure.auth.factory.telegram import WebAppUserDTOFactory, WebAppChatDTOFactory, \
    get_message_from_factory
import pytest
from aiogram.types import Chat, User
from core.di.bot import DIBot
from domain.auth_profile.enums import AuthProviderType
from interfaces.bot.telegram import TelegramBot
from interfaces.event_broker.kafka_bot import broker
from tests.t_interfaces.abstract.base_client import BaseClientTest


class TestTgBot(BaseClientTest):
    @pytest.fixture(scope="session")
    def bot_with_logging(self) -> tuple[TelegramBot, list]:
        log: list[str] = []

        async def logger(*args: tuple, **kwargs: dict) -> None:
            log.append(str(args[1]))

        TelegramBot._send_message = logger
        DIBot.register(TelegramBot, AuthProviderType.TELEGRAM)
        return TelegramBot.get_instance(), log

    @pytest.fixture(scope="function")
    async def kafka_worker(self, bot_with_logging: tuple[TelegramBot, list]) -> AsyncGenerator:
        task = asyncio.create_task(broker._run())
        yield
        task.cancel()

    @pytest.fixture(scope="function")
    def user_and_chat(self) -> tuple[User, Chat]:
        user: User = WebAppUserDTOFactory.build()
        chat: Chat = WebAppChatDTOFactory.build(id=user.id)
        return user, chat

    async def auth_user(self, client: AsyncClient, user_id: int) -> AuthResponseDTO:
        fake_user_telegram_data = self._get_auth_telegram_provider_data(user_id=user_id)
        auth_response = await client.post(self.route_auth_telegram, json=fake_user_telegram_data.model_dump())
        return AuthResponseDTO.model_validate(auth_response.json())

    @staticmethod
    async def check_messages_in_log(log: list[str], messages: list[str], timeout: int = 15) -> None:
        def normalize(text: str) -> str:
            return re.sub(r"\s+", " ", text.strip())

        while len(log) < len(messages) and timeout > 0:
            await asyncio.sleep(1)
            timeout -= 1
        assert len(log) == len(messages)
        for message, log_text in zip(messages, log):
            assert normalize(message) == normalize(log_text)
        log.clear()

    @pytest.mark.asyncio
    async def test_start_and_start_bonus(self,
                                         bot_with_logging: tuple[TelegramBot, list],
                                         user_and_chat: tuple[User, Chat],
                                         client: AsyncClient,
                                         kafka_worker: AsyncGenerator
                                         ) -> None:
        start = monotonic()
        bot, log = bot_with_logging
        user, chat = user_and_chat
        # start message
        start_message = get_message_from_factory("/start", user, chat)
        await bot.start(*(start_message,), **dict())
        auth_response = await self.auth_user(client, user.id)
        account = auth_response.account
        await self.check_messages_in_log(log, [GetBotMessages.start_for_new(AccountEntity(**account.model_dump()))])
        await asyncio.sleep(5)
        # first start bonus
        start_bonus_message = get_message_from_factory("/start_bonus", user, chat)
        await bot.start_bonus(*(start_bonus_message,), **dict())
        await self.check_messages_in_log(log, [
            GetBotMessages.start_bonus_requested(),
            GetBotMessages.add_credits_start_bonus(settings.credits_start_bonus)
        ])
        account_request = await client.get(self.route_me, headers=self._get_auth_headers(auth_response.token))
        assert account_request.status_code == 200
        account = AccountDTO.model_validate(account_request.json())
        assert account.credits == settings.credits_start_bonus
        # second start bonus / failure
        await bot.start_bonus(*(start_bonus_message,), **dict())
        await self.check_messages_in_log(log, [
            GetBotMessages.start_bonus_requested(),
            GetBotMessages.start_bonus_already_sended()
        ])
        # start message with different message after 10 secons after first start message
        while monotonic() - start < 11:
            await asyncio.sleep(1)
        await bot.start(*(start_message,), **dict())
        await self.check_messages_in_log(log, [GetBotMessages.start_for_exist(AccountEntity(**account.model_dump()))])
