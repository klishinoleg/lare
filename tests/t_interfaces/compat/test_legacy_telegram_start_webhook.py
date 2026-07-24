from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from domain.auth_profile.enums import AuthProviderType
from infrastructure.repository.tortoise.models import (
    AccountModel,
    AuthProfileModel,
)


@pytest.mark.asyncio
async def test_legacy_telegram_webhook_start_creates_and_reuses_account(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-telegram-start-webhook.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    settings.web_app_url = "https://lang-reader.test/"

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            first_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106301,
                    "message": {
                        "message_id": 8301,
                        "date": 1,
                        "chat": {"id": 9106301, "type": "private"},
                        "from": {
                            "id": 9106301,
                            "is_bot": False,
                            "first_name": "Start",
                            "last_name": "User",
                            "username": "start_webhook",
                            "language_code": "en",
                        },
                        "text": "/start",
                    },
                },
            )
            second_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106302,
                    "message": {
                        "message_id": 8302,
                        "date": 1,
                        "chat": {"id": 9106301, "type": "private"},
                        "from": {
                            "id": 9106301,
                            "is_bot": False,
                            "first_name": "Start",
                            "last_name": "User",
                            "username": "start_webhook",
                            "language_code": "en",
                        },
                        "text": "/start",
                    },
                },
            )

        assert first_response.status_code == 200
        first_payload = first_response.json()
        assert first_payload["success"] is True
        assert first_payload["handled"] == "start"
        assert first_payload["is_new"] is True
        assert first_payload["web_app_url"] == "https://lang-reader.test/"
        assert first_payload["keyboard"] == [
            [{"text": "Open WebApp", "web_app": "https://lang-reader.test/"}]
        ]
        assert "Welcome to Lazy Reader" in first_payload["text"]
        assert "/start_bonus" in first_payload["text"]

        assert second_response.status_code == 200
        second_payload = second_response.json()
        assert second_payload["success"] is True
        assert second_payload["handled"] == "start"
        assert second_payload["is_new"] is False
        assert second_payload["account_id"] == first_payload["account_id"]
        assert "Thank you for using" in second_payload["text"]

        account = await AccountModel.get(id=first_payload["account_id"])
        profile = await AuthProfileModel.get(
            account_id=account.id,
            provider_type=AuthProviderType.TELEGRAM,
        )
        account_count = await AccountModel.all().count()

        assert account.username == "TG:9106301:start_webhook"
        assert account.public_name == "Start User"
        assert profile.provider_id == "9106301"
        assert profile.language_code == "en"
        assert account_count == 1
    finally:
        await close_tortoise()
