from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from application.events.handlers_register.finance import register_finance_main_brokers
from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from domain.finance.enums.transaction_type import TransactionType
from infrastructure.broker.mock.broker import MockEventBroker
from infrastructure.broker.mock.publisher import MockPublisher
from infrastructure.repository.tortoise.models import (
    AccountModel,
    AccountTransactionModel,
)


@pytest.mark.asyncio
async def test_legacy_telegram_webhook_start_bonus_adds_credits_once(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-telegram-start-bonus-webhook.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    settings.credits_start_bonus = 100
    MockPublisher.clear_events()
    MockEventBroker.subscribers.clear()

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        register_finance_main_brokers(EventBrokerTypes.MOCK, bills=False)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9106201,
                            "username": "start_bonus_webhook",
                            "first_name": "Start",
                            "last_name": "Bonus",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            account_id = auth_response.json()["account"]["id"]

            first_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106201,
                    "message": {
                        "message_id": 8201,
                        "date": 1,
                        "chat": {"id": 9106201, "type": "private"},
                        "from": {
                            "id": 9106201,
                            "is_bot": False,
                            "first_name": "Start",
                            "username": "start_bonus_webhook",
                        },
                        "text": "/start_bonus",
                    },
                },
            )
            second_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106202,
                    "message": {
                        "message_id": 8202,
                        "date": 1,
                        "chat": {"id": 9106201, "type": "private"},
                        "from": {
                            "id": 9106201,
                            "is_bot": False,
                            "first_name": "Start",
                            "username": "start_bonus_webhook",
                        },
                        "text": "/start_bonus",
                    },
                },
            )

        assert first_response.status_code == 200
        assert first_response.json() == {
            "success": True,
            "handled": "start_bonus",
            "credits_amount": 100.0,
            "message": "Start bonus granted",
        }
        assert second_response.status_code == 200
        assert second_response.json() == {
            "success": False,
            "handled": "start_bonus",
            "credits_amount": 0.0,
            "message": "Start bonus already exists",
        }

        account = await AccountModel.get(id=account_id)
        transactions = await AccountTransactionModel.filter(
            account_id=account_id,
            transaction_type=TransactionType.START_BONUS,
        )

        assert account.credits == Decimal("100.00")
        assert len(transactions) == 1
        assert transactions[0].credits_amount == Decimal("100.00")
    finally:
        await close_tortoise()
