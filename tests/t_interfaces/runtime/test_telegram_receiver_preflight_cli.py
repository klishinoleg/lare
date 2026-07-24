from __future__ import annotations

import json
from io import StringIO

import pytest

from tests.t_infrastructure.runtime.test_telegram_receiver_preflight import FakeTelegramBotApi


@pytest.mark.asyncio
async def test_telegram_receiver_preflight_cli_reports_missing_token_without_api_calls() -> None:
    from interfaces.runtime import telegram_receiver_preflight_cli

    stdout = StringIO()
    api = FakeTelegramBotApi(webhook_url="")

    exit_code = await telegram_receiver_preflight_cli.run(
        [],
        stdout=stdout,
        token_provider=lambda: "",
        api_factory=lambda token: api,
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["token_present"] is False
    assert payload["issues"] == ["token_missing"]
    assert api.calls == []


@pytest.mark.asyncio
async def test_telegram_receiver_preflight_cli_outputs_safe_matching_receiver_json() -> None:
    from interfaces.runtime import telegram_receiver_preflight_cli

    stdout = StringIO()
    desired_url = "https://lang-reader-server.ngrok.app/api/v1/telegram/update/"

    exit_code = await telegram_receiver_preflight_cli.run(
        ["--desired-webhook-url", desired_url],
        stdout=stdout,
        token_provider=lambda: "123456:secret-token",
        api_factory=lambda token: FakeTelegramBotApi(webhook_url=desired_url),
    )
    output = stdout.getvalue()
    payload = json.loads(output)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["bot_username"] == "lazy_reader_dev_bot"
    assert payload["receiver_ready"] is True
    assert payload["desired_webhook_url"] == desired_url
    assert "secret-token" not in output
