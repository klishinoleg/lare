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
                    "id": 9103201,
                    "username": "text_part_list",
                    "first_name": "TextPart",
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
        json={"name": "Text part list book", "language": 1},
    )
    assert book_response.status_code == 200
    book_id = book_response.json()["id"]

    chapter_response = await client.post(
        f"/api/v1/book/{book_id}/add_chapter/",
        headers=headers,
        json={
            "name": "Text part list chapter",
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
async def legacy_text_part_list_app(tmp_path):
    db_path = tmp_path / "legacy-text-part-list.sqlite3"
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
async def test_legacy_text_part_list_returns_created_items_for_reducer_load_list(
    legacy_text_part_list_app,
) -> None:
    transport = ASGITransport(app=legacy_text_part_list_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers, context = await _create_chapter_context(client)
        create_response = await client.post(
            "/api/v1/text_part/create_from_indexes/",
            headers=headers,
            json={
                "indexes": [item["id"] for item in context["content"][:2]],
                "action": "translate",
                "translate_type": "translate",
            },
        )
        assert create_response.status_code == 200
        created_text_part = create_response.json()
        text_part_id = created_text_part["id"]
        assert created_text_part["translate"]
        assert created_text_part["words"] == []

        words_response = await client.post(
            "/api/v1/text_part/create_from_indexes/",
            headers=headers,
            json={
                "indexes": [item["id"] for item in context["content"][:2]],
                "action": "translate",
                "translate_type": "words",
            },
        )
        assert words_response.status_code == 200
        assert words_response.json()["id"] == text_part_id

        list_response = await client.get("/api/v1/text_part/", headers=headers)

    assert list_response.status_code == 200
    text_parts = list_response.json()
    assert isinstance(text_parts, list)
    assert [item["id"] for item in text_parts] == [text_part_id]
    assert text_parts[0]["chapter_id"] == context["chapter_id"]
    assert text_parts[0]["translate"]
    assert text_parts[0]["words"]


@pytest.mark.asyncio
async def test_legacy_text_part_create_supports_generic_reducer_create_item(
    legacy_text_part_list_app,
) -> None:
    transport = ASGITransport(app=legacy_text_part_list_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers, context = await _create_chapter_context(client)

        create_response = await client.post(
            "/api/v1/text_part/",
            headers=headers,
            json={
                "name": "manual selected text",
                "chapter_id": context["chapter_id"],
                "translate": "manual selected translation",
                "description": "manual selected note",
                "transliteration": "manual selected transliteration",
            },
        )
        list_response = await client.get("/api/v1/text_part/", headers=headers)

    assert create_response.status_code == 200
    data = create_response.json()
    assert data["name"] == "manual selected text"
    assert data["chapter_id"] == context["chapter_id"]
    assert data["translate"]["translate"] == "manual selected translation"
    assert data["translate"]["description"] == "manual selected note"
    assert data["transliteration"] == "manual selected transliteration"
    assert data["words"] == []

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [data["id"]]


@pytest.mark.asyncio
async def test_legacy_text_part_update_supports_generic_reducer_update_item(
    legacy_text_part_list_app,
) -> None:
    transport = ASGITransport(app=legacy_text_part_list_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers, context = await _create_chapter_context(client)
        create_response = await client.post(
            "/api/v1/text_part/create_from_indexes/",
            headers=headers,
            json={
                "indexes": [item["id"] for item in context["content"][:2]],
                "action": "translate",
                "translate_type": "words",
            },
        )
        assert create_response.status_code == 200
        text_part_id = create_response.json()["id"]

        update_response = await client.patch(
            f"/api/v1/text_part/{text_part_id}/",
            headers=headers,
            json={
                "name": "custom selected text",
                "translate": "custom translation",
                "description": "custom note",
                "transliteration": "custom transliteration",
            },
        )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == text_part_id
    assert data["name"] == "custom selected text"
    assert data["translate"]["translate"] == "custom translation"
    assert data["translate"]["description"] == "custom note"
    assert data["transliteration"] == "custom transliteration"
    assert data["words"]


@pytest.mark.asyncio
async def test_legacy_text_part_delete_supports_work_translate_delete_button(
    legacy_text_part_list_app,
) -> None:
    transport = ASGITransport(app=legacy_text_part_list_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers, context = await _create_chapter_context(client)
        create_response = await client.post(
            "/api/v1/text_part/create_from_indexes/",
            headers=headers,
            json={
                "indexes": [item["id"] for item in context["content"][:2]],
                "action": "translate",
            },
        )
        assert create_response.status_code == 200
        text_part_id = create_response.json()["id"]

        delete_response = await client.delete(
            f"/api/v1/text_part/{text_part_id}/",
            headers=headers,
        )
        list_response = await client.get("/api/v1/text_part/", headers=headers)
        detail_response = await client.get(
            f"/api/v1/text_part/{text_part_id}/",
            headers=headers,
        )
        chapter_response = await client.get(
            f"/api/v1/chapter/{context['chapter_id']}/",
            headers=headers,
        )

    assert delete_response.status_code == 200
    assert delete_response.json() == {"id": text_part_id}
    assert list_response.status_code == 200
    assert list_response.json() == []
    assert detail_response.status_code == 404
    assert chapter_response.status_code == 200
    assert all(item.get("t") != text_part_id for item in chapter_response.json()["content"])
