from aiogram.types import LabeledPrice
from application.account.services import AccountService
from core.messages.exceptions import GetExMessages
from core.messages.finance import GetFinanceMessages
from domain.auth_profile.enums import AuthProviderType
from domain.finance.contexts.create_bill_context import CreateBillContext
from domain.finance.enums.currency import Currency
from core.enums.payment.payment_service import PaymentService
from domain.finance.exceptions import PaymentCreationError
from infrastructure.payment.base import BasePaymentProvider
from core.datatypes.payment_provider_options import TelegramStatsProviderOptions
from core.config import settings
from aiogram import Bot


class TelegramStarsProvider(BasePaymentProvider[TelegramStatsProviderOptions]):
    payment_service = PaymentService.TG_STARS
    options: TelegramStatsProviderOptions | None

    @classmethod
    async def _prepare_options(cls, create_bill_context: CreateBillContext,
                               account_service: AccountService) -> TelegramStatsProviderOptions:
        telegram_profile = await account_service.get_auth_profile_by_auth_provider(
            create_bill_context.account_id,
            AuthProviderType.TELEGRAM
        )
        if not telegram_profile:
            raise PaymentCreationError(
                GetExMessages.for_make_payment_you_have_to_create_auth_profile(AuthProviderType.TELEGRAM))
        return TelegramStatsProviderOptions(
            chat_id=int(telegram_profile.provider_id),
            title=GetFinanceMessages.payment_title(),
            description=GetFinanceMessages.payment_description(),
            prices=[LabeledPrice(
                label=GetFinanceMessages.credits_amount(create_bill_context.credits_amount),
                amount=create_bill_context.cost)
            ]
        )

    @classmethod
    async def _create_payment(cls,
                              create_bill_context: CreateBillContext,
                              options: TelegramStatsProviderOptions
                              ) -> str | None:
        bot = Bot(token=settings.tg_bot_token)
        invoice = {
            "chat_id": options.chat_id,
            "title": options.title,
            "description": options.description,
            "payload": str(create_bill_context.bill_id),
            "provider_token": settings.tg_payment_provider_token,
            "currency": Currency.STAR.value,
            "prices": options.prices,
            "need_name": False,
            "need_phone_number": False,
            "need_email": False,
            "need_shipping_address": False,
        }
        await bot.send_invoice(**invoice)
        return None
