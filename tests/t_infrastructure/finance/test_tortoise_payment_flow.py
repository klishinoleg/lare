from __future__ import annotations

from decimal import Decimal

import pytest

from application.events.handlers_register.finance import register_finance_main_brokers
from application.finance.utils.bill_factory import bill_successful_event
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


@pytest.mark.asyncio
async def test_tortoise_bill_success_creates_transaction_and_updates_credits(tmp_path) -> None:
    db_path = tmp_path / "finance-payment.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    MockPublisher.clear_events()

    await init_tortoise()
    try:
        register_finance_main_brokers(EventBrokerTypes.MOCK)
        account = await AccountModel.create(username="payment-flow", credits=0)
        bill = await BillModel.create(
            account_id=account.id,
            credits_amount=Decimal("10.00"),
            cost=10,
            currency=Currency.STAR,
            payment_service=PaymentService.TG_STARS,
            payment_data={},
        )

        await bill_successful_event(
            bill_id=bill.id,
            payment_data={"charge": "ok"},
            transaction="charge-ok",
            token=None,
        )

        await account.refresh_from_db()
        await bill.refresh_from_db()
        transactions = await AccountTransactionModel.filter(account_id=account.id)

        assert bill.success_time is not None
        assert bill.transaction == "charge-ok"
        assert len(transactions) == 1
        assert float(account.credits) == 10.0
    finally:
        await close_tortoise()
