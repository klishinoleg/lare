from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from core.enums.payment.payment_service import PaymentService
from domain.access_role.enums.roles import AccessRole
from domain.finance.enums.currency import Currency
from infrastructure.repository.tortoise.models import (
    AccessRoleModel,
    BillModel,
)


@pytest.mark.asyncio
async def test_legacy_telegram_webhook_stats_command_requires_admin_and_returns_bill_stats(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-telegram-admin-stats-webhook.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            admin_auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9106501,
                            "username": "stats_admin",
                            "first_name": "Stats",
                            "last_name": "Admin",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert admin_auth_response.status_code == 200
            admin_account_id = admin_auth_response.json()["account"]["id"]
            await AccessRoleModel.create(
                account_id=admin_account_id,
                role=AccessRole.SUPERUSER,
            )

            user_auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9106502,
                            "username": "stats_regular",
                            "first_name": "Stats",
                            "last_name": "Regular",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert user_auth_response.status_code == 200
            user_account_id = user_auth_response.json()["account"]["id"]

            await BillModel.create(
                account_id=user_account_id,
                credits_amount=Decimal("21.00"),
                cost=21,
                currency=Currency.STAR,
                payment_service=PaymentService.TG_STARS,
                payment_data={},
                success_time=datetime.now(timezone.utc),
                transaction="paid-stars",
            )
            await BillModel.create(
                account_id=user_account_id,
                credits_amount=Decimal("9.00"),
                cost=9,
                currency=Currency.STAR,
                payment_service=PaymentService.TG_STARS,
                payment_data={},
            )
            await BillModel.create(
                account_id=user_account_id,
                credits_amount=Decimal("100.00"),
                cost=100,
                currency=Currency.RUB,
                payment_service=PaymentService.MANUAL,
                payment_data={},
                success_time=datetime.now(timezone.utc),
                transaction="manual-paid",
            )

            regular_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106501,
                    "message": {
                        "message_id": 8501,
                        "date": 1,
                        "chat": {"id": 9106502, "type": "private"},
                        "from": {
                            "id": 9106502,
                            "is_bot": False,
                            "first_name": "Stats",
                            "username": "stats_regular",
                        },
                        "text": "/stats",
                    },
                },
            )
            admin_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106502,
                    "message": {
                        "message_id": 8502,
                        "date": 1,
                        "chat": {"id": 9106501, "type": "private"},
                        "from": {
                            "id": 9106501,
                            "is_bot": False,
                            "first_name": "Stats",
                            "username": "stats_admin",
                        },
                        "text": "/stats",
                    },
                },
            )

        assert regular_response.status_code == 403
        assert regular_response.json()["detail"] == "telegram admin is required"

        assert admin_response.status_code == 200
        payload = admin_response.json()
        assert payload["success"] is True
        assert payload["handled"] == "payment_stats"
        assert payload["payment_service"] == PaymentService.TG_STARS.value
        assert payload["summary"] == {
            "profit": 21,
            "avg": 21,
            "paid": 1,
            "total": 2,
        }
        assert "Summary" in payload["text"]
        assert "Profit: 21" in payload["text"]
        assert "Paid: 1" in payload["text"]
        assert "Total: 2" in payload["text"]
    finally:
        await close_tortoise()
