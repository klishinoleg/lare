from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes


@pytest.mark.asyncio
async def test_legacy_telegram_start_referral_links_new_bot_account(tmp_path) -> None:
    db_path = tmp_path / "legacy-telegram-referral-webhook.sqlite3"
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
            owner_auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9106901,
                            "username": "ref_owner",
                            "first_name": "Referral",
                            "last_name": "Owner",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert owner_auth_response.status_code == 200
            owner_auth = owner_auth_response.json()
            owner_headers = {"Authorization": f"Token {owner_auth['token']}"}

            referral_code_response = await client.get(
                "/api/v1/transaction/get_referral_code/",
                headers=owner_headers,
            )
            assert referral_code_response.status_code == 200
            referral_code_payload = referral_code_response.json()
            referral_code = referral_code_payload["code"]

            start_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106901,
                    "message": {
                        "message_id": 8901,
                        "date": 1,
                        "chat": {"id": 9106902, "type": "private"},
                        "from": {
                            "id": 9106902,
                            "is_bot": False,
                            "first_name": "Referral",
                            "last_name": "Friend",
                            "username": "ref_friend",
                            "language_code": "en",
                        },
                        "text": f"/start ref_{referral_code}",
                    },
                },
            )
            duplicate_start_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99106902,
                    "message": {
                        "message_id": 8902,
                        "date": 1,
                        "chat": {"id": 9106902, "type": "private"},
                        "from": {
                            "id": 9106902,
                            "is_bot": False,
                            "first_name": "Referral",
                            "last_name": "Friend",
                            "username": "ref_friend",
                            "language_code": "en",
                        },
                        "text": f"/start ref_{referral_code}",
                    },
                },
            )
            referrals_response = await client.get(
                "/api/v1/transaction/get_referrals/",
                headers=owner_headers,
            )

        assert referral_code == f"lr_{owner_auth['account']['id']}"
        assert referral_code_payload["referral_url"].endswith(f"?start=ref_{referral_code}")

        assert start_response.status_code == 200
        start_payload = start_response.json()
        assert start_payload["success"] is True
        assert start_payload["handled"] == "start"
        assert start_payload["is_new"] is True
        assert start_payload["referral_added"] is True

        assert duplicate_start_response.status_code == 200
        duplicate_payload = duplicate_start_response.json()
        assert duplicate_payload["is_new"] is False
        assert duplicate_payload["referral_added"] is False

        assert referrals_response.status_code == 200
        referrals = referrals_response.json()
        assert len(referrals) == 1
        assert referrals[0]["referral"]["username"] == "TG:9106902:ref_friend"
        assert referrals[0]["referral"]["full_name"] == "Referral Friend"
        assert referrals[0]["earned_amount"] == 0
    finally:
        await close_tortoise()
