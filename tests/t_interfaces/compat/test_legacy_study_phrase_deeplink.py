from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes


@pytest.mark.asyncio
async def test_legacy_study_phrase_detail_supports_bot_deeplink_to_chapter_word(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy-study-phrase-deeplink.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"

    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9105001,
                            "username": "study_deeplink",
                            "first_name": "Study",
                            "last_name": "Deeplink",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            headers = {"Authorization": f"Token {auth_response.json()['token']}"}

            book_response = await client.post(
                "/api/v1/book/",
                headers=headers,
                json={"name": "Study deeplink book", "language": 1},
            )
            assert book_response.status_code == 200
            book_id = book_response.json()["id"]

            add_chapter_response = await client.post(
                f"/api/v1/book/{book_id}/add_chapter/",
                headers=headers,
                json={
                    "name": "Study deeplink chapter",
                    "chapter_input": {"text": "hello ! world"},
                },
            )
            assert add_chapter_response.status_code == 200
            chapter_id = add_chapter_response.json()["chapters"][0]["id"]

            chapter_response = await client.get(
                f"/api/v1/chapter/{chapter_id}/",
                headers=headers,
            )
            assert chapter_response.status_code == 200
            world_token = next(
                item for item in chapter_response.json()["content"] if item["name"] == "world"
            )

            word_response = await client.get(
                f"/api/v1/word/{world_token['w']}/",
                headers=headers,
            )
            assert word_response.status_code == 200
            world_word_id = word_response.json()["word"]["id"]
            world_translate_id = word_response.json()["id"]
            assert world_word_id == world_token["w"]
            assert isinstance(world_translate_id, int)

            create_study_response = await client.post(
                "/api/v1/study_phrase/",
                headers=headers,
                json={
                    "chapter_id": chapter_id,
                    "word_id": world_word_id,
                    "is_active": True,
                },
            )
            assert create_study_response.status_code == 200
            study_id = create_study_response.json()["id"]

            study_response = await client.get(
                f"/api/v1/study_phrase/{study_id}/",
                headers=headers,
            )
            refreshed_chapter_response = await client.get(
                f"/api/v1/chapter/{chapter_id}/",
                headers=headers,
            )

        assert study_response.status_code == 200
        study = study_response.json()
        assert study["id"] == study_id
        assert study["chapter_id"] == chapter_id
        assert study["word"]["id"] == world_word_id
        assert study["word"]["translate"]["id"] == world_translate_id

        refreshed_world_token = next(
            item for item in refreshed_chapter_response.json()["content"] if item["name"] == "world"
        )
        assert refreshed_world_token["w"] == study["word"]["id"]
    finally:
        await close_tortoise()
