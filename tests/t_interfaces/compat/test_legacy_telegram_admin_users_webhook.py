from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from domain.access_role.enums.roles import AccessRole
from infrastructure.repository.tortoise.models import AccessRoleModel


@pytest.mark.asyncio
async def test_legacy_telegram_webhook_users_command_requires_admin_and_returns_counts(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-telegram-admin-users-webhook.sqlite3"
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
                            "id": 9106401,
                            "username": "users_admin",
                            "first_name": "Users",
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
                            "id": 9106402,
                            "username": "users_regular",
                            "first_name": "Users",
                            "last_name": "Regular",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert user_auth_response.status_code == 200
            user_account_id = user_auth_response.json()["account"]["id"]
            user_headers = {"Authorization": f"Token {user_auth_response.json()['token']}"}
            create_book_response = await client.post(
                "/api/v1/book/",
                headers=user_headers,
                json={"name": "Users stats book", "language": 1},
            )
            assert create_book_response.status_code == 200

            regular_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106401,
                    "message": {
                        "message_id": 8401,
                        "date": 1,
                        "chat": {"id": 9106402, "type": "private"},
                        "from": {
                            "id": 9106402,
                            "is_bot": False,
                            "first_name": "Users",
                            "username": "users_regular",
                        },
                        "text": "/users",
                    },
                },
            )
            admin_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106402,
                    "message": {
                        "message_id": 8402,
                        "date": 1,
                        "chat": {"id": 9106401, "type": "private"},
                        "from": {
                            "id": 9106401,
                            "is_bot": False,
                            "first_name": "Users",
                            "username": "users_admin",
                        },
                        "text": "/users",
                    },
                },
            )

        assert regular_response.status_code == 403
        assert regular_response.json()["detail"] == "telegram admin is required"

        assert admin_response.status_code == 200
        payload = admin_response.json()
        assert payload["success"] is True
        assert payload["handled"] == "users_stats"
        assert payload["totals"] == {"accounts": 2, "books": 1}
        assert any(f"#{user_account_id}" in row for row in payload["users"])
        assert any("@users_regular" in row for row in payload["users"])
        assert "Total (15d)" in payload["text"]
        assert "Recent users" in payload["text"]
        assert f"#{user_account_id}" in payload["text"]
        assert "accounts" in payload["text"]
        assert "books" in payload["text"]
    finally:
        await close_tortoise()
