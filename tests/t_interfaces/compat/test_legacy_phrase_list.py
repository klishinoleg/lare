from __future__ import annotations

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from application.events.handlers_register.finance import register_finance_main_brokers
from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from infrastructure.broker.mock.broker import MockEventBroker
from infrastructure.broker.mock.publisher import MockPublisher


async def _create_chapter_context(
    client: AsyncClient,
) -> tuple[dict[str, str], dict[str, Any]]:
    auth_response = await client.post(
        "/api/v1/account/telegram_auth/",
        json={
            "auth_data": {
                "user": {
                    "id": 9103101,
                    "username": "phrase_list",
                    "first_name": "Phrase",
                    "last_name": "List",
                    "language_code": "en",
                }
            }
        },
    )
    assert auth_response.status_code == 200
    auth_data = auth_response.json()
    headers = {"Authorization": f"Token {auth_data['token']}"}

    book_response = await client.post(
        "/api/v1/book/",
        headers=headers,
        json={"name": "Phrase list book", "language": 1},
    )
    assert book_response.status_code == 200
    book_id = book_response.json()["id"]

    chapter_response = await client.post(
        f"/api/v1/book/{book_id}/add_chapter/",
        headers=headers,
        json={
            "name": "Phrase list chapter",
            "chapter_input": {"text": "hello brave async world"},
        },
    )
    assert chapter_response.status_code == 200
    chapter_id = chapter_response.json()["chapters"][0]["id"]

    chapter_detail_response = await client.get(
        f"/api/v1/chapter/{chapter_id}/",
        headers=headers,
    )
    assert chapter_detail_response.status_code == 200
    content = [item for item in chapter_detail_response.json()["content"] if item.get("w")]
    assert len(content) >= 2
    return headers, {"chapter_id": chapter_id, "content": content}


@pytest.fixture
async def legacy_phrase_list_app(tmp_path):
    db_path = tmp_path / "legacy-phrase-list.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    MockPublisher.clear_events()
    MockEventBroker.subscribers.clear()

    from interfaces.fast_api.main import app

    await init_tortoise()
    register_finance_main_brokers(EventBrokerTypes.MOCK, bills=False)
    try:
        yield app
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_legacy_phrase_list_returns_created_phrases_for_reducer_load_list(
    legacy_phrase_list_app,
) -> None:
    transport = ASGITransport(app=legacy_phrase_list_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers, context = await _create_chapter_context(client)
        indexes = [item["id"] for item in context["content"][:2]]
        text_part_response = await client.post(
            "/api/v1/text_part/create_from_indexes/",
            headers=headers,
            json={
                "indexes": indexes,
                "action": "translate",
                "translate_type": "words",
            },
        )
        assert text_part_response.status_code == 200

        phrase_response = await client.post(
            "/api/v1/phrase/create_from_indexes/",
            headers=headers,
            json={"indexes_list": [indexes]},
        )
        assert phrase_response.status_code == 200
        phrase_id = phrase_response.json()[0]["id"]

        list_response = await client.get("/api/v1/phrase/", headers=headers)

    assert list_response.status_code == 200
    phrases = list_response.json()
    assert isinstance(phrases, list)
    assert [item["id"] for item in phrases] == [phrase_id]
    assert phrases[0]["chapter_id"] == context["chapter_id"]
    assert phrases[0]["words"]


@pytest.mark.asyncio
async def test_legacy_phrase_create_from_indexes_uses_matching_text_part_when_links_overlap(
    legacy_phrase_list_app,
) -> None:
    transport = ASGITransport(app=legacy_phrase_list_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers, context = await _create_chapter_context(client)
        full_indexes = [item["id"] for item in context["content"][:4]]
        phrase_indexes = full_indexes[:2]
        full_text_part_response = await client.post(
            "/api/v1/text_part/create_from_indexes/",
            headers=headers,
            json={
                "indexes": full_indexes,
                "action": "translate",
                "translate_type": "translate",
            },
        )
        assert full_text_part_response.status_code == 200
        exact_text_part_response = await client.post(
            "/api/v1/text_part/create_from_indexes/",
            headers=headers,
            json={
                "indexes": phrase_indexes,
                "action": "translate",
                "translate_type": "words",
            },
        )
        assert exact_text_part_response.status_code == 200
        exact_text_part_id = exact_text_part_response.json()["id"]

        phrase_response = await client.post(
            "/api/v1/phrase/create_from_indexes/",
            headers=headers,
            json={"indexes_list": [phrase_indexes]},
        )

    assert phrase_response.status_code == 200
    phrase = phrase_response.json()[0]
    assert phrase["text_part_id"] == exact_text_part_id
    assert phrase["text_part"] == exact_text_part_id
    assert phrase["words"]


@pytest.mark.asyncio
async def test_legacy_phrase_create_supports_generic_reducer_create_item(
    legacy_phrase_list_app,
) -> None:
    transport = ASGITransport(app=legacy_phrase_list_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers, context = await _create_chapter_context(client)

        create_response = await client.post(
            "/api/v1/phrase/",
            headers=headers,
            json={
                "name": "manual phrase",
                "chapter_id": context["chapter_id"],
                "translate": "manual phrase translation",
                "description": "manual phrase note",
                "transliteration": "manual phrase transliteration",
            },
        )

        list_response = await client.get("/api/v1/phrase/", headers=headers)

    assert create_response.status_code == 200
    data = create_response.json()
    assert data["name"] == "manual phrase"
    assert data["chapter_id"] == context["chapter_id"]
    assert data["translate"]["translate"] == "manual phrase translation"
    assert data["translate"]["description"] == "manual phrase note"
    assert data["transliteration"] == "manual phrase transliteration"
    assert data["words"] == []

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [data["id"]]


@pytest.mark.asyncio
async def test_legacy_phrase_update_supports_generic_reducer_update_item(
    legacy_phrase_list_app,
) -> None:
    transport = ASGITransport(app=legacy_phrase_list_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers, context = await _create_chapter_context(client)
        indexes = [item["id"] for item in context["content"][:2]]
        text_part_response = await client.post(
            "/api/v1/text_part/create_from_indexes/",
            headers=headers,
            json={
                "indexes": indexes,
                "action": "translate",
                "translate_type": "words",
            },
        )
        assert text_part_response.status_code == 200

        phrase_response = await client.post(
            "/api/v1/phrase/create_from_indexes/",
            headers=headers,
            json={"indexes_list": [indexes]},
        )
        assert phrase_response.status_code == 200
        phrase_id = phrase_response.json()[0]["id"]

        update_response = await client.patch(
            f"/api/v1/phrase/{phrase_id}/",
            headers=headers,
            json={
                "name": "custom phrase text",
                "translate": "custom phrase translation",
                "description": "custom phrase note",
                "transliteration": "custom phrase transliteration",
            },
        )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == phrase_id
    assert data["name"] == "custom phrase text"
    assert data["translate"]["translate"] == "custom phrase translation"
    assert data["translate"]["description"] == "custom phrase note"
    assert data["transliteration"] == "custom phrase transliteration"
    assert data["words"]


@pytest.mark.asyncio
async def test_legacy_phrase_delete_supports_work_translate_delete_button(
    legacy_phrase_list_app,
) -> None:
    transport = ASGITransport(app=legacy_phrase_list_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers, context = await _create_chapter_context(client)
        text_part_response = await client.post(
            "/api/v1/text_part/create_from_indexes/",
            headers=headers,
            json={
                "indexes": [item["id"] for item in context["content"][:2]],
                "action": "translate",
            },
        )
        assert text_part_response.status_code == 200
        text_part_id = text_part_response.json()["id"]
        phrase_response = await client.post(
            "/api/v1/phrase/create_from_indexes/",
            headers=headers,
            json={"indexes_list": [[item["id"] for item in context["content"][:2]]]},
        )
        assert phrase_response.status_code == 200
        phrase_id = phrase_response.json()[0]["id"]

        delete_response = await client.delete(
            f"/api/v1/phrase/{phrase_id}/",
            headers=headers,
        )
        list_response = await client.get("/api/v1/phrase/", headers=headers)
        detail_response = await client.get(
            f"/api/v1/phrase/{phrase_id}/",
            headers=headers,
        )
        text_part_phrases_response = await client.get(
            f"/api/v1/phrase/load_for_text_part/?text_part={text_part_id}",
            headers=headers,
        )

    assert delete_response.status_code == 200
    assert delete_response.json() == {"id": phrase_id}
    assert list_response.status_code == 200
    assert list_response.json() == []
    assert detail_response.status_code == 404
    assert text_part_phrases_response.status_code == 200
    assert text_part_phrases_response.json() == []
