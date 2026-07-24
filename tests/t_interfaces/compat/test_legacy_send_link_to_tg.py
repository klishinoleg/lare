from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes


@pytest.mark.asyncio
async def test_legacy_send_link_to_tg_sends_webapp_button(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "legacy-send-link-to-tg.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = "test-token"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    settings.web_app_url = "https://lang-reader.test/"

    sent_messages: list[dict] = []

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeBot:
        def __init__(self, token: str):
            self.token = token
            self.session = FakeSession()

        async def send_message(self, **kwargs):
            sent_messages.append({"token": self.token, **kwargs})

    from interfaces.fast_api.main import app
    from interfaces.fast_api.routers import compat

    monkeypatch.setattr(compat, "Bot", FakeBot)

    await init_tortoise()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9107001,
                            "username": "send_link",
                            "first_name": "Send",
                            "last_name": "Link",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            headers = {"Authorization": f"Token {auth_response.json()['token']}"}

            link_response = await client.post(
                "/api/v1/account/send_link_to_tg/",
                headers=headers,
                json={"text": "Open this section", "path": "/reader/book/42"},
            )

        assert link_response.status_code == 200
        assert link_response.json() == {
            "detail": "Link sent successfully",
            "success": True,
            "web_app_url": "https://lang-reader.test/reader/book/42",
            "keyboard": [
                [{"text": "Open WebApp", "web_app": "https://lang-reader.test/reader/book/42"}]
            ],
        }
        assert len(sent_messages) == 1
        assert sent_messages[0]["token"] == "test-token"
        assert sent_messages[0]["chat_id"] == 9107001
        assert sent_messages[0]["text"] == "Open this section"
        button = sent_messages[0]["reply_markup"].inline_keyboard[0][0]
        assert button.text == "Open WebApp"
        assert button.web_app.url == "https://lang-reader.test/reader/book/42"
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_send_link_to_tg_dry_run_does_not_send_message(
    monkeypatch,
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-send-link-to-tg-dry-run.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = "test-token"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    settings.web_app_url = "https://lang-reader.test/"

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeBot:
        def __init__(self, token: str):
            self.token = token
            self.session = FakeSession()

        async def send_message(self, **kwargs):
            raise AssertionError("dry-run must not send a Telegram message")

    from interfaces.fast_api.main import app
    from interfaces.fast_api.routers import compat

    monkeypatch.setattr(compat, "Bot", FakeBot)

    await init_tortoise()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9107002,
                            "username": "send_link_dry",
                            "first_name": "Send",
                            "last_name": "Dry",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            headers = {"Authorization": f"Token {auth_response.json()['token']}"}

            link_response = await client.post(
                "/api/v1/account/send_link_to_tg/",
                headers=headers,
                json={
                    "text": "Preview this section",
                    "path": "/reader/book/99",
                    "dry_run": True,
                },
            )

        assert link_response.status_code == 200
        assert link_response.json() == {
            "detail": "Link sent successfully",
            "success": True,
            "dry_run": True,
            "web_app_url": "https://lang-reader.test/reader/book/99",
            "keyboard": [
                [{"text": "Open WebApp", "web_app": "https://lang-reader.test/reader/book/99"}]
            ],
        }
    finally:
        await close_tortoise()
