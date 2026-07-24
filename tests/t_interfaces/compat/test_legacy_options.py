from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from interfaces.fast_api.main import app


@pytest.mark.asyncio
async def test_legacy_options_exposes_form_metadata() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        book_response = await client.options("/api/v1/book/")
        chapter_response = await client.options("/api/v1/chapter/")
        transaction_response = await client.options("/api/v1/transaction/")

    assert book_response.status_code == 200
    book_actions = book_response.json()["actions"]
    assert book_actions["POST"]["name"]["required"] is True
    assert book_actions["POST"]["language"]["type"] == "integer"
    assert book_actions["PATCH"]["description"]["required"] is False

    assert chapter_response.status_code == 200
    chapter_actions = chapter_response.json()["actions"]
    assert chapter_actions["POST"]["text"]["required"] is True
    assert chapter_actions["PATCH"]["percent"]["type"] == "integer"

    assert transaction_response.status_code == 200
    transaction_actions = transaction_response.json()["actions"]
    assert transaction_actions["POST"]["cost"]["required"] is True


@pytest.mark.asyncio
async def test_legacy_options_keeps_safe_fallback_for_unknown_resources() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.options("/api/v1/unknown/")

    assert response.status_code == 200
    assert response.json()["actions"] == {"POST": {}, "PATCH": {}, "PUT": {}, "DELETE": {}}
