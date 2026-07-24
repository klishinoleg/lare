from __future__ import annotations

from decimal import Decimal

import pytest
from aiogram import Bot
from aiogram.types import SuccessfulPayment

from application.events.handlers_register.finance import register_finance_main_brokers
from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from core.enums.payment.payment_service import PaymentService
from domain.finance.enums.currency import Currency
from infrastructure.broker.mock.publisher import MockPublisher
from infrastructure.repository.tortoise.models import (
    AccountModel,
    AccountTransactionModel,
    BillModel,
)
from interfaces.bot.telegram import TelegramBot


@pytest.mark.asyncio
async def test_telegram_bot_successful_payment_confirms_bill(tmp_path) -> None:
    db_path = tmp_path / "telegram-payment-success.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = "123456:TESTTOKEN"
    MockPublisher.clear_events()

    await init_tortoise()
    try:
        register_finance_main_brokers(EventBrokerTypes.MOCK)
        account = await AccountModel.create(username="telegram-payment", credits=0)
        bill = await BillModel.create(
            account_id=account.id,
            credits_amount=Decimal("15.00"),
            cost=15,
            currency=Currency.STAR,
            payment_service=PaymentService.TG_STARS,
            payment_data={},
        )
        bot = TelegramBot(bot=Bot(token=settings.tg_bot_token))
        successful_payment = SuccessfulPayment(
            currency=Currency.STAR.value,
            total_amount=15,
            invoice_payload=str(bill.id),
            telegram_payment_charge_id="tg-charge-ok",
            provider_payment_charge_id="provider-charge-ok",
        )

        await bot.payment_success(message=None, successful_payment=successful_payment)

        await account.refresh_from_db()
        await bill.refresh_from_db()
        transactions = await AccountTransactionModel.filter(account_id=account.id)

        assert bill.success_time is not None
        assert bill.transaction == "tg-charge-ok"
        assert len(transactions) == 1
        assert float(account.credits) == 15.0
        await bot.bot.session.close()
    finally:
        await close_tortoise()
