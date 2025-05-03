import asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, FSInputFile, InputMediaPhoto, \
    PreCheckoutQuery, SuccessfulPayment
from urllib.parse import urlencode
from core.config import settings
from core.enums.bot.bot_types import BotTypes
from domain.auth_profile.enums import AuthProviderType
from infrastructure.auth.dtos.telegram import TelegramAuthInitDataDTO, TelegramProviderDataDTO, TelegramWebAppInitDTO
from interfaces.bot.base_bot_interface import BaseBotInterface, Keyboard
import re
from typing import Pattern, Dict, Any
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery
from core.registrators.init_auth_providers import register_auth_providers
from core.db import init_tortoise


class CallbackRegexFilter(BaseFilter):
    def __init__(self, pattern: str | Pattern[str]) -> None:
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        self.pattern: Pattern[str] = pattern

    async def __call__(self, callback_query: CallbackQuery) -> Dict[str, Any] | bool:
        if not callback_query.data:
            return False

        match = self.pattern.match(callback_query.data)
        if match:
            return match.groupdict()
        return False


class TelegramBot(BaseBotInterface[Message, Bot, TelegramAuthInitDataDTO]):
    bot_type = BotTypes.TELEGRAM
    dp = Dispatcher()

    @BaseBotInterface.with_auth()
    async def start(self, *args: tuple, **kwargs: dict) -> None:
        await self._base_start()

    @BaseBotInterface.with_auth()
    async def task(self, message: Message, callback: CallbackQuery, task_type: str, *args: tuple,
                   **kwargs: dict) -> None:
        await self._base_task_create(task_type)

    @BaseBotInterface.with_auth()
    async def start_bonus(self, *args: tuple, **kwargs: dict) -> None:
        await self._base_start_bonus()

    @BaseBotInterface.with_auth()
    async def reset_tasks(self, *args: tuple, **kwargs: dict) -> None:
        await self._base_reset_tasks()

    @BaseBotInterface.with_auth()
    async def manual_credits(self, callback: CallbackQuery, *args: tuple, **kwargs: dict) -> None:
        await self._base_bill_manual_create(message=callback.data)

    @BaseBotInterface.with_auth()
    async def confirm_manual_credits(self, bill_id: int, answer: str, *args: tuple, **kwargs: dict) -> None:
        await self._base_bill_manual_confirm(bill_id, answer == "yes")

    async def pre_checkout(self, pre_checkout_query: PreCheckoutQuery, *args: tuple, **kwargs: dict) -> None:
        bill_id = int(pre_checkout_query.invoice_payload)
        result = await self._base_payment_checkout(bill_id=bill_id)
        await pre_checkout_query.answer(ok=result.success, error_message=result.message)

    async def payment_success(self, message: Message, successful_payment: SuccessfulPayment, *args: tuple,
                              **kwargs: dict) -> None:
        bill_id = int(successful_payment.invoice_payload)
        transaction = successful_payment.telegram_payment_charge_id
        payment_data = successful_payment.model_dump()
        await self._base_payment_successful(bill_id=bill_id, transaction=transaction, payment_data=payment_data)

    async def set_handlers(self) -> None:
        self.dp.message.register(self.start, CommandStart())
        self.dp.message.register(self.start_bonus, Command("start_bonus"))
        self.dp.message.register(self.reset_tasks, Command("reset_tasks"))
        self.dp.callback_query.register(self.task, CallbackRegexFilter(r"action_(?P<task_type>\d+)"))
        self.dp.message.register(self.manual_credits, F.regexp(r"^credits:.*$"))
        self.dp.callback_query.register(self.confirm_manual_credits,
                                        CallbackRegexFilter(r"manual_bill_(?P<bill_id>\d+)_(?P<answer>yes|no)"))
        self.dp.pre_checkout_query.register(self.pre_checkout)
        self.dp.message.register(self.payment_success, F.successful_payment.exists())

    async def run(self) -> None:
        async with self.bot.session:
            await self.dp.start_polling(self.bot)

    async def _get_language(self, message: Message, **kwargs: dict) -> str:
        language_code = message.from_user.language_code if message.from_user else None
        return language_code or settings.language_code

    async def get_auth_data(self, message: Message, **kwargs: dict) -> TelegramAuthInitDataDTO:
        init_data_unsafe = TelegramWebAppInitDTO(
            chat=message.chat,
            user=message.from_user
        )

        return TelegramAuthInitDataDTO(
            provider_type=AuthProviderType.TELEGRAM,
            provider_data=TelegramProviderDataDTO(
                init_data=urlencode(init_data_unsafe.model_dump()),
                init_data_unsafe=init_data_unsafe
            )
        )

    @classmethod
    def get_bot(cls) -> Bot:
        return Bot(token=settings.tg_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))

    @staticmethod
    def get_tg_keyboard(keyboard: Keyboard | None) -> InlineKeyboardMarkup | None:
        if keyboard is None:
            return None
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=button.title,
                        callback_data=button.callback,
                        web_app=WebAppInfo(url=button.webapp) if button.webapp else None,
                        url=button.url,
                    )
                    for button in line.buttons
                ]
                for line in keyboard.lines
            ]
        )

    async def send_message(self,
                           text: str, keyboard: Keyboard | None = None,
                           audio: Path | None = None, video: Path | None = None,
                           images: list[Path] | None = None, chat_id: int | None = None,
                           filename: str | None = None
                           ) -> None:
        async with self.bot.session:
            await self._send_message(text, keyboard, audio, video, images, chat_id, filename)

    async def _send_message(self, text: str, keyboard: Keyboard | None = None,
                            audio: Path | None = None, video: Path | None = None,
                            images: list[Path] | None = None, chat_id: int | None = None,
                            filename: str | None = None) -> None:
        chat_id = await self._get_chat_id(chat_id)
        if audio:
            await self.bot.send_audio(
                chat_id=chat_id,
                audio=FSInputFile(audio, filename=filename),
                reply_markup=self.get_tg_keyboard(keyboard),
                caption=text,
            )
        elif video:
            await self.bot.send_video(
                chat_id=chat_id,
                video=FSInputFile(video, filename=filename),
                reply_markup=self.get_tg_keyboard(keyboard),
                caption=text,
            )
        elif images:
            if len(images) == 1:
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=FSInputFile(images[0], filename=filename),
                    reply_markup=self.get_tg_keyboard(keyboard),
                    caption=text,
                )
            else:
                await self.bot.send_media_group(
                    chat_id=chat_id,
                    media=[InputMediaPhoto(media=FSInputFile(image)) for image in images]
                )
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=self.get_tg_keyboard(keyboard),
                )
        else:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=self.get_tg_keyboard(keyboard),
            )

    async def delete_message(self, message_id: int | None = None, chat_id: int | None = None) -> None:
        await self.bot.delete_message(
            chat_id=await self._get_chat_id(chat_id),
            message_id=message_id or await self._get_message_id(message_id)
        )

    async def modify_message(self, text: str, keyboard: Keyboard | None = None,
                             chat_id: int | None = None, message_id: int | None = None) -> None:
        await self.bot.edit_message_text(
            chat_id=await self._get_chat_id(chat_id),
            message_id=await self._get_message_id(message_id),
            text=text,
            reply_markup=self.get_tg_keyboard(keyboard),
        )

    async def _get_message_sender(self, message: Message, **kwargs: dict) -> Message:
        return message

    async def _get_message_id(self, message_id: int | None = None) -> int | None:
        if message_id:
            return message_id
        if self.message_sender:
            return self.message_sender.message_id
        if self.auth_profile:
            return int(self.auth_profile.provider_id)
        raise ValueError("No message id source")

    async def _get_chat_id(self, chat_id: int | None = None) -> int | None:
        if chat_id:
            return chat_id
        if self.message_sender:
            return self.message_sender.chat.id
        if self.auth_profile:
            return int(self.auth_profile.provider_id)
        raise ValueError("No chat id source")


async def main() -> None:
    register_auth_providers()
    await init_tortoise()
    bot = TelegramBot.get_instance()
    await bot.set_handlers()
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
