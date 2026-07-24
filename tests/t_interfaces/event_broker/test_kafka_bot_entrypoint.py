from __future__ import annotations

import pytest


@pytest.mark.anyio
async def test_kafka_bot_startup_registers_bots_for_faststream(monkeypatch: pytest.MonkeyPatch) -> None:
    from interfaces.event_broker import kafka_bot

    calls: list[str] = []

    async def fake_initial_before_start() -> None:
        calls.append("initial_before_start")

    def fake_register_bots() -> None:
        calls.append("register_bots")

    monkeypatch.setattr(kafka_bot, "initial_before_start", fake_initial_before_start)
    monkeypatch.setattr(kafka_bot, "register_bots", fake_register_bots)

    await kafka_bot.broker_before_start()

    assert calls == ["register_bots", "initial_before_start"]
