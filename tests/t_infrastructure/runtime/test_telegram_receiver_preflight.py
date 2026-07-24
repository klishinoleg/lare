from __future__ import annotations

import pytest


class FakeTelegramBotApi:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url
        self.calls: list[str] = []

    async def get_me(self) -> dict[str, object]:
        self.calls.append("get_me")
        return {
            "ok": True,
            "result": {
                "id": 123456,
                "is_bot": True,
                "username": "lazy_reader_dev_bot",
            },
        }

    async def get_webhook_info(self) -> dict[str, object]:
        self.calls.append("get_webhook_info")
        return {
            "ok": True,
            "result": {
                "url": self.webhook_url,
                "pending_update_count": 0,
                "last_error_message": "",
            },
        }


@pytest.mark.asyncio
async def test_telegram_receiver_preflight_does_not_call_api_without_token() -> None:
    from infrastructure.runtime.telegram_receiver_preflight import (
        TelegramReceiverPreflightConfig,
        run_telegram_receiver_preflight,
    )

    api = FakeTelegramBotApi(webhook_url="")

    result = await run_telegram_receiver_preflight(
        TelegramReceiverPreflightConfig(
            token="",
            desired_webhook_url="https://lang-reader-server.ngrok.app/api/v1/telegram/update/",
        ),
        api_factory=lambda token: api,
    )

    assert result.ok is False
    assert result.token_present is False
    assert result.receiver_ready is False
    assert result.issues == ("token_missing",)
    assert api.calls == []


@pytest.mark.asyncio
async def test_telegram_receiver_preflight_reports_matching_webhook() -> None:
    from infrastructure.runtime.telegram_receiver_preflight import (
        TelegramReceiverPreflightConfig,
        run_telegram_receiver_preflight,
    )

    desired_url = "https://lang-reader-server.ngrok.app/api/v1/telegram/update/"
    api = FakeTelegramBotApi(webhook_url=desired_url)

    result = await run_telegram_receiver_preflight(
        TelegramReceiverPreflightConfig(
            token="123456:secret-token",
            desired_webhook_url=desired_url,
        ),
        api_factory=lambda token: api,
    )

    assert result.ok is True
    assert result.token_present is True
    assert result.bot_username == "lazy_reader_dev_bot"
    assert result.current_webhook_url == desired_url
    assert result.desired_webhook_url == desired_url
    assert result.receiver_ready is True
    assert result.pending_update_count == 0
    assert result.issues == ()
    assert "secret-token" not in str(result.to_dict())


@pytest.mark.asyncio
async def test_telegram_receiver_preflight_reports_receiver_mismatch() -> None:
    from infrastructure.runtime.telegram_receiver_preflight import (
        TelegramReceiverPreflightConfig,
        run_telegram_receiver_preflight,
    )

    api = FakeTelegramBotApi(webhook_url="https://server.lazy-reader.com/api/v1/telegram/update/")

    result = await run_telegram_receiver_preflight(
        TelegramReceiverPreflightConfig(
            token="123456:secret-token",
            desired_webhook_url="https://lang-reader-server.ngrok.app/api/v1/telegram/update/",
        ),
        api_factory=lambda token: api,
    )

    assert result.ok is False
    assert result.receiver_ready is False
    assert result.issues == ("webhook_mismatch",)
