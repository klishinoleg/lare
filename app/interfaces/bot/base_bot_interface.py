from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Self
from pydantic import BaseModel, ValidationError
from application.access_control.services import Accessor
from application.auth.services.auth_via_profile import AuthViaProfileService
from application.finance.utils.manual_bill import parse_manual_bill_message, confirm_manual_bill, delete_manual_bill, \
    PATTERN_CREDITS_MESSAGE
from application.finance.utils.bill_factory import bill_successful_event, create_bill_event, check_bill_for_payment
from core.i18n import activate
from application.finance.utils.transaction_factory import publish_start_bonus_transaction
from core.enums.bot.bot_types import BotTypes
from core.messages.bot import GetBotMessages
from core.messages.common import GetComMessages
from core.messages.finance import GetFinanceMessages
from domain.finance.exceptions import BillRetrySuccessError

if TYPE_CHECKING:
    from application.auth.dtos import AuthInitDataDTO, AuthResponseDTO
    from domain.account.entities import AccountEntity
    from domain.auth_profile.entities import AuthProfileEntity


class PaymentCheckoutResult(BaseModel):
    success: bool
    message: str


class PaymentSuccessResult(BaseModel):
    success: bool
    message: str


class Button(BaseModel):
    title: str
    url: str | None = None
    callback: str | None = None
    webapp: str | None = None


class Line(BaseModel):
    buttons: list[Button]


class Keyboard(BaseModel):
    lines: list[Line]


def only_auth() -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self: "BaseBotInterface", *args: tuple, **kwargs: dict) -> Any:
            if not self.account or (not self.message_sender and not self.bot):
                raise PermissionError
            return await func(self, *args, **kwargs)

        return wrapper

    return decorator


class BaseBotInterface[MSG, BOT, AUIDTO: "AuthInitDataDTO"](ABC):
    """
    Unified interface for bot systems to perform core business interactions
    with the application layer via common entrypoints.
    """

    bot_type: BotTypes

    def __init__(self, bot: BOT) -> None:
        self.bot: BOT = bot
        self.message_sender: MSG | None = None
        self.auth_result: "AuthResponseDTO" | None = None
        self.auth_profile: "AuthProfileEntity" | None = None
        self.account: "AccountEntity" | None = None

    @abstractmethod
    async def get_auth_data(self, *args: tuple, **kwargs: dict) -> AUIDTO:
        ...

    @abstractmethod
    async def send_message(self,
                           text: str, keyboard: Keyboard | None = None,
                           audio: Path | None = None,
                           video: Path | None = None,
                           images: list[Path] | None = None,
                           chat_id: int | str | None = None,
                           filename: str | None = None
                           ) -> None:
        ...

    @abstractmethod
    async def _send_message(self,
                            text: str, keyboard: Keyboard | None = None,
                            audio: Path | None = None,
                            video: Path | None = None,
                            images: list[Path] | None = None,
                            chat_id: int | str | None = None,
                            filename: str | None = None
                            ) -> None:
        ...

    @abstractmethod
    async def _get_language(self, *args: tuple, **kwargs: dict) -> str:
        ...

    @abstractmethod
    async def delete_message(self, message_id: int | None = None,
                             chat_id: int | str | None = None) -> None:
        ...

    @abstractmethod
    async def modify_message(self, text: str, keyboard: Keyboard | None = None,
                             chat_id: int | str | None = None, message_id: int | None = None) -> None:
        ...

    @abstractmethod
    async def _get_message_sender(self, *args: tuple, **kwargs: dict) -> MSG | None:
        ...

    @abstractmethod
    async def _get_message_id(self, message_id: int | str | None = None) -> int | str | None:
        ...

    @abstractmethod
    async def _get_chat_id(self, chat_id: int | str | None = None) -> int | str | None:
        ...

    @classmethod
    @abstractmethod
    def get_bot(cls) -> BOT:
        ...

    @abstractmethod
    async def set_handlers(self) -> None:
        ...

    @abstractmethod
    async def run(self) -> None:
        ...

    @only_auth()
    async def _base_start(self) -> None:
        """Start bot session for a user (depends on auth type)."""
        if not self.account:
            raise AttributeError
        if self.account.created_at > datetime.now(tz=timezone.utc) - timedelta(seconds=10):
            return await self._send_message(GetBotMessages.start_for_new(self.account))
        return await self._send_message(GetBotMessages.start_for_exist(self.account))

    @only_auth()
    async def _base_task_create(self, task_type: str) -> None:
        """Send request to create a task (e.g. translation, summary)."""
        raise NotImplementedError  # TODO: Create tasks method

    @only_auth()
    async def _base_reset_tasks(self) -> None:
        """Reset or cancel all pending/active tasks."""
        raise NotImplementedError  # TODO: Rest tasks method

    @only_auth()
    async def _base_start_bonus(self) -> None:
        """Issue a start bonus to the account."""
        if not self.account:
            raise AttributeError
        await publish_start_bonus_transaction(self.account.id)
        await self._send_message(GetBotMessages.start_bonus_requested())

    @only_auth()
    async def _base_task_rate(self, task_id: int, rate: int) -> None:
        """Send task rating (feedback mechanism)."""
        raise NotImplementedError  # TODO: Rest tasks method

    @staticmethod
    async def _base_payment_checkout(bill_id: int) -> PaymentCheckoutResult:
        """Validate a payment before processing checkout."""
        try:
            await check_bill_for_payment(bill_id)
        except BillRetrySuccessError as e:
            return PaymentCheckoutResult(success=False, message=str(e))
        return PaymentCheckoutResult(success=True, message="ok")

    @staticmethod
    async def _base_payment_successful(bill_id: int, transaction: str,
                                       payment_data: dict, token: str | None = None) -> PaymentSuccessResult:
        """Handle a successful payment. Should trigger a Transaction and BillSuccess event."""
        try:
            await bill_successful_event(bill_id=bill_id, transaction=transaction, payment_data=payment_data,
                                        token=token)
        except BillRetrySuccessError as e:
            return PaymentSuccessResult(success=False, message=str(e))
        return PaymentSuccessResult(success=True, message="ok")

    @only_auth()
    async def _base_bill_manual_create(self, message: str) -> None:
        """Manually create a bill (e.g. via admin panel or bot)."""
        if not await Accessor.is_superuser(self.account):
            await self.delete_message()
            return

        try:
            account, dto = await parse_manual_bill_message(message)
        except ValidationError as e:
            return await self._send_message(text=str(e))

        bill_id = await create_bill_event(dto)

        await self._send_message(
            text=GetBotMessages.confirm_manual_bill(account),
            keyboard=Keyboard(lines=[
                Line(buttons=[
                    Button(title=GetComMessages.yes(), callback=f"manual_bill_{bill_id}_yes"),
                    Button(title=GetComMessages.no(), callback=f"manual_bill_{bill_id}_no")
                ])
            ])
        )

    @only_auth()
    async def _base_bill_manual_confirm(self, bill_id: int, confirm: bool) -> None:
        """Confirm manual payment and publish BillSuccessfulEvent."""
        if confirm:
            try:
                await confirm_manual_bill(
                    bill_id=bill_id, account=self.account,
                    transaction=f"{self.bot_type.value}:{await self._get_chat_id()}:{await self._get_message_id()}")
                await self._send_message(GetFinanceMessages.bill_has_been_confirmed())
            except BillRetrySuccessError as e:
                await self._send_message(text=str(e))
        else:
            await delete_manual_bill(bill_id=bill_id)
            await self._send_message(GetFinanceMessages.bill_has_been_removed())

    @classmethod
    async def get_with_auth_provider(cls, account: "AccountEntity", auth_profile: "AuthProfileEntity") -> Self:
        bot = cls(bot=cls.get_bot())
        bot.account = account
        bot.auth_profile = auth_profile
        return bot

    @classmethod
    def get_instance(cls) -> Self:
        return cls(bot=cls.get_bot())

    @staticmethod
    def with_auth() -> Callable:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(self: Any, *args: tuple, **kwargs: dict) -> Any:
                self.auth_result = await AuthViaProfileService().authenticate(
                    await self.get_auth_data(*args, **kwargs), is_safe=True)
                self.account = self.auth_result.account
                self.message_sender = await self._get_message_sender(*args, **kwargs)
                activate(await self._get_language(*args, **kwargs))
                return await func(self, *args, **kwargs)

            return wrapper

        return decorator

    @classmethod
    def get_credits_message_pattern(cls) -> str:
        return PATTERN_CREDITS_MESSAGE
