from __future__ import annotations

import json
from io import StringIO

import pytest

from tests.t_infrastructure.ai.test_reader_provider_smoke import FakeReaderProvider


@pytest.mark.asyncio
async def test_reader_ai_smoke_cli_outputs_safe_json() -> None:
    from interfaces.runtime import reader_ai_smoke_cli

    stdout = StringIO()

    exit_code = await reader_ai_smoke_cli.run(
        [],
        stdout=stdout,
        provider_factory=lambda: FakeReaderProvider(provider_name="openai"),
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["include_media"] is False
    assert [step["name"] for step in payload["steps"]] == [
        "translate_text",
        "answer_dialog",
        "explain_word",
    ]
    assert "translated" not in stdout.getvalue()


@pytest.mark.asyncio
async def test_reader_ai_smoke_cli_fails_when_external_required_but_local_used() -> None:
    from interfaces.runtime import reader_ai_smoke_cli

    stdout = StringIO()

    exit_code = await reader_ai_smoke_cli.run(
        ["--require-external"],
        stdout=stdout,
        provider_factory=lambda: FakeReaderProvider(provider_name="local"),
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["required_provider"] == "openai"
    assert payload["steps"][0]["provider"] == "local"


@pytest.mark.asyncio
async def test_reader_ai_smoke_cli_can_require_named_provider() -> None:
    from interfaces.runtime import reader_ai_smoke_cli

    stdout = StringIO()

    exit_code = await reader_ai_smoke_cli.run(
        ["--require-provider", "deepseek"],
        stdout=stdout,
        provider_factory=lambda: FakeReaderProvider(provider_name="deepseek"),
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["required_provider"] == "deepseek"
