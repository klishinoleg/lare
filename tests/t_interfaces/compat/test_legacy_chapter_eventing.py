from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from application.book.events.chapter_events import ChapterCreateRequestedEvent
from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from infrastructure.repository.tortoise.models import WordChapterModel


@pytest.mark.asyncio
async def test_legacy_add_chapter_publishes_background_parse_event(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "legacy-add-chapter-eventing.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"

    published: list[tuple[object, str | None]] = []

    class FakePublisher:
        @classmethod
        async def publish(cls, payload, group_id=None, broker_type=None):
            published.append((payload, group_id))

    from interfaces.fast_api.main import app
    from interfaces.fast_api.routers import compat

    monkeypatch.setattr(compat, "DIPublisher", FakePublisher, raising=False)

    await init_tortoise()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9107101,
                            "username": "chapter_eventing",
                            "first_name": "Chapter",
                            "last_name": "Eventing",
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
                json={"name": "Evented compatibility book", "language": 1},
            )
            assert book_response.status_code == 200
            book_id = book_response.json()["id"]

            add_response = await client.post(
                f"/api/v1/book/{book_id}/add_chapter/",
                headers=headers,
                json={
                    "name": "Evented chapter",
                    "chapter_input": {"text": "Async parsing should happen in the worker."},
                },
            )
            chapter_id = add_response.json()["chapters"][0]["id"]
            chapter_response = await client.get(f"/api/v1/chapter/{chapter_id}/", headers=headers)

        assert add_response.status_code == 200
        chapter = add_response.json()["chapters"][0]
        assert chapter["is_ready"] is False
        assert chapter_response.status_code == 200
        assert chapter_response.json()["content"] == []
        assert await WordChapterModel.filter(chapter_id=chapter["id"]).count() == 0

        assert len(published) == 1
        event, group_id = published[0]
        assert isinstance(event, ChapterCreateRequestedEvent)
        assert event.book_id == book_id
        assert event.chapter_id == chapter["id"]
        assert event.text == "Async parsing should happen in the worker."
        assert event.pid == f"compat:chapter:{chapter['id']}"
        assert group_id == f"book:{book_id}"
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_chapter_detail_does_not_translate_every_word(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "legacy-chapter-detail-no-word-translate.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.tg_bot_token = ""
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"

    from infrastructure.repository.tortoise.models import ChapterModel
    from interfaces.fast_api.main import app
    from interfaces.fast_api.routers import compat

    async def fail_if_word_translate_is_forced(*args, **kwargs):
        raise AssertionError("chapter detail must not translate every word")

    await init_tortoise()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9107102,
                            "username": "chapter_no_word_translate",
                            "first_name": "Chapter",
                            "last_name": "NoTranslate",
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
                json={"name": "Fast chapter detail book", "language": 1},
            )
            assert book_response.status_code == 200
            book_id = book_response.json()["id"]

            add_response = await client.post(
                f"/api/v1/book/{book_id}/add_chapter/",
                headers=headers,
                json={
                    "name": "Fast chapter detail",
                    "chapter_input": {"text": "hello brave world"},
                },
            )
            assert add_response.status_code == 200
            chapter_id = add_response.json()["chapters"][0]["id"]
            chapter = await ChapterModel.get(id=chapter_id)
            await compat._tokenize_chapter(chapter, "hello brave world")

            monkeypatch.setattr(
                compat,
                "_ensure_word_translate",
                fail_if_word_translate_is_forced,
                raising=False,
            )
            chapter_response = await client.get(f"/api/v1/chapter/{chapter_id}/", headers=headers)

        assert chapter_response.status_code == 200
        content = [item for item in chapter_response.json()["content"] if item.get("w")]
        assert len(content) == 3
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_chapter_source_url_can_be_created_and_updated(tmp_path) -> None:
    db_path = tmp_path / "legacy-chapter-source-url.sqlite3"
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
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9107103,
                            "username": "chapter_source_url",
                            "first_name": "Chapter",
                            "last_name": "SourceUrl",
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
                json={"name": "Source URL book", "language": 1},
            )
            assert book_response.status_code == 200
            book_id = book_response.json()["id"]

            add_response = await client.post(
                f"/api/v1/book/{book_id}/add_chapter/",
                headers=headers,
                json={
                    "name": "Podcast chapter",
                    "source_url": "https://www.youtube.com/watch?v=source-one",
                    "chapter_input": {"text": "This chapter came from a podcast."},
                },
            )
            assert add_response.status_code == 200
            chapter = add_response.json()["chapters"][0]
            chapter_id = chapter["id"]

            detail_response = await client.get(
                f"/api/v1/chapter/{chapter_id}/",
                headers=headers,
            )
            patch_response = await client.patch(
                f"/api/v1/chapter/{chapter_id}/",
                headers=headers,
                json={"input_url": "https://youtu.be/source-two"},
            )

        assert chapter["source_url"] == "https://www.youtube.com/watch?v=source-one"
        assert chapter["input_url"] == "https://www.youtube.com/watch?v=source-one"
        assert detail_response.status_code == 200
        assert detail_response.json()["source_url"] == chapter["source_url"]
        assert detail_response.json()["input_url"] == chapter["input_url"]
        assert patch_response.status_code == 200
        assert patch_response.json()["source_url"] == "https://youtu.be/source-two"
        assert patch_response.json()["input_url"] == "https://youtu.be/source-two"
    finally:
        await close_tortoise()
