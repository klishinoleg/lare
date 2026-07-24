from __future__ import annotations

import json
from io import StringIO

import pytest

from tests.t_infrastructure.runtime.test_telegram_receiver_switch import (
    FakeSwitchTelegramBotApi,
)


@pytest.mark.asyncio
async def test_telegram_receiver_switch_cli_defaults_to_plan_only() -> None:
    from interfaces.runtime import telegram_receiver_switch_cli

    stdout = StringIO()
    api = FakeSwitchTelegramBotApi(
        webhook_url="https://server.lazy-reader.com/api/v1/telegram/update/",
    )

    exit_code = await telegram_receiver_switch_cli.run(
        [],
        stdout=stdout,
        token_provider=lambda: "123456:secret-token",
        api_factory=lambda token: api,
    )
    output = stdout.getvalue()
    payload = json.loads(output)

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["apply_requested"] is False
    assert payload["applied"] is False
    assert payload["issues"] == ["apply_required"]
    assert "secret-token" not in output
    assert all(call[0] != "set_webhook" for call in api.calls)


@pytest.mark.asyncio
async def test_telegram_receiver_switch_cli_apply_requires_confirmation_flag() -> None:
    from interfaces.runtime import telegram_receiver_switch_cli

    stdout = StringIO()
    api = FakeSwitchTelegramBotApi()

    exit_code = await telegram_receiver_switch_cli.run(
        ["--apply"],
        stdout=stdout,
        token_provider=lambda: "123456:secret-token",
        api_factory=lambda token: api,
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 2
    assert payload["issues"] == ["confirmation_required"]
    assert all(call[0] != "set_webhook" for call in api.calls)


@pytest.mark.asyncio
async def test_telegram_receiver_switch_cli_can_apply_with_explicit_confirmation() -> None:
    from interfaces.runtime import telegram_receiver_switch_cli

    stdout = StringIO()
    api = FakeSwitchTelegramBotApi()

    exit_code = await telegram_receiver_switch_cli.run(
        ["--apply", "--confirm-receiver-switch", "--drop-pending-updates"],
        stdout=stdout,
        token_provider=lambda: "123456:secret-token",
        api_factory=lambda token: api,
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["applied"] is True
    assert any(call[0] == "set_webhook" for call in api.calls)
