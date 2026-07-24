from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes


@pytest.mark.asyncio
async def test_legacy_telegram_callback_rates_study_phrase_log(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "legacy-study-phrase-bot-rating.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = "test-token"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"

    from infrastructure.repository.tortoise.models import CompatStudyPhraseLogModel
    from interfaces.fast_api.main import app
    from interfaces.fast_api.routers import compat

    class FakeTelegramSession:
        async def __aenter__(self) -> "FakeTelegramSession":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

    class FakeTelegramBot:
        callback_answers: list[dict[str, object]] = []

        def __init__(self, token: str) -> None:
            assert token == "test-token"
            self.session = FakeTelegramSession()

        async def answer_callback_query(self, **kwargs: object) -> None:
            self.callback_answers.append(kwargs)

    monkeypatch.setattr(compat, "Bot", FakeTelegramBot)

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
                            "username": "study_rating",
                            "first_name": "Study",
                            "last_name": "Rating",
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
                json={"name": "Study rating book", "language": 1},
            )
            assert book_response.status_code == 200
            book_id = book_response.json()["id"]

            add_chapter_response = await client.post(
                f"/api/v1/book/{book_id}/add_chapter/",
                headers=headers,
                json={
                    "name": "Study rating chapter",
                    "chapter_input": {"text": "hello rating world"},
                },
            )
            assert add_chapter_response.status_code == 200
            chapter_id = add_chapter_response.json()["chapters"][0]["id"]

            chapter_response = await client.get(
                f"/api/v1/chapter/{chapter_id}/",
                headers=headers,
            )
            assert chapter_response.status_code == 200
            rating_token = next(
                item for item in chapter_response.json()["content"] if item["name"] == "rating"
            )

            create_study_response = await client.post(
                "/api/v1/study_phrase/",
                headers=headers,
                json={
                    "chapter_id": chapter_id,
                    "word_id": rating_token["w"],
                    "is_active": True,
                },
            )
            assert create_study_response.status_code == 200
            study_id = create_study_response.json()["id"]

            log = await CompatStudyPhraseLogModel.create(
                study_phrase_id=study_id,
                study_type="forward",
            )

            callback_response = await client.post(
                "/api/v1/telegram/update/",
                json={
                    "update_id": 99107001,
                    "callback_query": {
                        "id": "callback-study-rating-1",
                        "from": {
                            "id": 9107001,
                            "is_bot": False,
                            "first_name": "Study",
                            "username": "study_rating",
                            "language_code": "en",
                        },
                        "message": {
                            "message_id": 7107,
                            "date": 1,
                            "chat": {"id": 9107001, "type": "private"},
                        },
                        "data": f"study_phrase_{log.id}_5",
                    },
                },
            )

            study_response = await client.get(
                f"/api/v1/study_phrase/{study_id}/",
                headers=headers,
            )

        assert callback_response.status_code == 200
        assert callback_response.json() == {
            "success": True,
            "handled": "study_phrase_rating",
            "study_phrase_id": study_id,
            "log_id": log.id,
            "rank": 5,
            "study_type": "forward",
        }
        assert FakeTelegramBot.callback_answers == [
            {
                "callback_query_id": "callback-study-rating-1",
                "text": "Saved: 5",
                "show_alert": False,
            }
        ]

        rated_log = await CompatStudyPhraseLogModel.get(id=log.id)
        study = study_response.json()
        assert rated_log.rank == 5
        assert study["success_logs"] == 1
        assert study["forward_average"] == 5
        assert study["reverse_average"] == 0
        assert study["audio_average"] == 0
        assert study["average"] == 5
    finally:
        await close_tortoise()
