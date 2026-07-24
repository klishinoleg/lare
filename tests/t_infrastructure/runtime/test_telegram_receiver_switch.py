from __future__ import annotations

import pytest


class FakeSwitchTelegramBotApi:
    def __init__(self, webhook_url: str = "") -> None:
        self.webhook_url = webhook_url
        self.calls: list[tuple[str, object]] = []

    async def get_webhook_info(self) -> dict[str, object]:
        self.calls.append(("get_webhook_info", None))
        return {
            "ok": True,
            "result": {
                "url": self.webhook_url,
                "pending_update_count": 0,
                "last_error_message": "",
            },
        }

    async def set_webhook(
        self,
        *,
        url: str,
        drop_pending_updates: bool,
    ) -> dict[str, object]:
        self.calls.append(
            (
                "set_webhook",
                {
                    "url": url,
                    "drop_pending_updates": drop_pending_updates,
                },
            )
        )
        self.webhook_url = url
        return {"ok": True, "result": True, "description": "Webhook was set"}


@pytest.mark.asyncio
async def test_telegram_receiver_switch_does_not_call_api_without_token() -> None:
    from infrastructure.runtime.telegram_receiver_switch import (
        TelegramReceiverSwitchConfig,
        run_telegram_receiver_switch,
    )

    api = FakeSwitchTelegramBotApi()

    result = await run_telegram_receiver_switch(
        TelegramReceiverSwitchConfig(
            token="",
            desired_webhook_url="https://lang-reader-server.ngrok.app/api/v1/telegram/update/",
        ),
        api_factory=lambda token: api,
    )

    assert result.ok is False
    assert result.token_present is False
    assert result.applied is False
    assert result.issues == ("token_missing",)
    assert api.calls == []


@pytest.mark.asyncio
async def test_telegram_receiver_switch_plans_without_setting_webhook_by_default() -> None:
    from infrastructure.runtime.telegram_receiver_switch import (
        TelegramReceiverSwitchConfig,
        run_telegram_receiver_switch,
    )

    api = FakeSwitchTelegramBotApi(
        webhook_url="https://server.lazy-reader.com/api/v1/telegram/update/",
    )

    result = await run_telegram_receiver_switch(
        TelegramReceiverSwitchConfig(
            token="123456:secret-token",
            desired_webhook_url="https://lang-reader-server.ngrok.app/api/v1/telegram/update/",
        ),
        api_factory=lambda token: api,
    )

    assert result.ok is False
    assert result.apply_requested is False
    assert result.applied is False
    assert result.action == "set_webhook"
    assert result.issues == ("apply_required",)
    assert api.calls == [("get_webhook_info", None)]
    assert "secret-token" not in str(result.to_dict())


@pytest.mark.asyncio
async def test_telegram_receiver_switch_requires_confirmation_before_apply() -> None:
    from infrastructure.runtime.telegram_receiver_switch import (
        TelegramReceiverSwitchConfig,
        run_telegram_receiver_switch,
    )

    api = FakeSwitchTelegramBotApi()

    result = await run_telegram_receiver_switch(
        TelegramReceiverSwitchConfig(
            token="123456:secret-token",
            desired_webhook_url="https://lang-reader-server.ngrok.app/api/v1/telegram/update/",
            apply=True,
            confirm_receiver_switch=False,
        ),
        api_factory=lambda token: api,
    )

    assert result.ok is False
    assert result.apply_requested is True
    assert result.applied is False
    assert result.issues == ("confirmation_required",)
    assert api.calls == [("get_webhook_info", None)]


@pytest.mark.asyncio
async def test_telegram_receiver_switch_applies_only_after_explicit_confirmation() -> None:
    from infrastructure.runtime.telegram_receiver_switch import (
        TelegramReceiverSwitchConfig,
        run_telegram_receiver_switch,
    )

    desired_url = "https://lang-reader-server.ngrok.app/api/v1/telegram/update/"
    api = FakeSwitchTelegramBotApi()

    result = await run_telegram_receiver_switch(
        TelegramReceiverSwitchConfig(
            token="123456:secret-token",
            desired_webhook_url=desired_url,
            apply=True,
            confirm_receiver_switch=True,
            drop_pending_updates=True,
        ),
        api_factory=lambda token: api,
    )

    assert result.ok is True
    assert result.applied is True
    assert result.action == "set_webhook"
    assert result.desired_webhook_url == desired_url
    assert result.issues == ()
    assert api.calls == [
        ("get_webhook_info", None),
        (
            "set_webhook",
            {
                "url": desired_url,
                "drop_pending_updates": True,
            },
        ),
    ]
