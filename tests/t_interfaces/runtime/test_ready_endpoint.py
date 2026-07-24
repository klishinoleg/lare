from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from interfaces.fast_api.main import app


@pytest.mark.asyncio
async def test_ready_endpoint_is_public_and_stable() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        root_response = await client.get("/ready")
        api_response = await client.get("/api/v1/ready")

    assert root_response.status_code == 200
    assert root_response.json() == {
        "status": "ok",
        "service": "lazy-reader-ddd",
    }
    assert api_response.status_code == 200
    assert api_response.json() == root_response.json()
