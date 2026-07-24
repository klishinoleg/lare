from __future__ import annotations

import json
from io import StringIO

from tests.t_infrastructure.runtime.test_compatibility_acceptance import (
    FakeSmokeResult,
    healthy_runtime_status,
)


def test_compatibility_acceptance_cli_outputs_safe_json() -> None:
    from interfaces.runtime import compatibility_acceptance_cli

    stdout = StringIO()

    exit_code = compatibility_acceptance_cli.run(
        ["--api-root", "https://lang-reader-server.ngrok.app/api/v1"],
        stdout=stdout,
        runtime_status_provider=healthy_runtime_status,
        frontend_contract_runner=lambda: FakeSmokeResult(True, "frontend"),
        reader_actions_runner=lambda: FakeSmokeResult(True, "reader"),
        legacy_compat_runner=lambda: FakeSmokeResult(True, "legacy"),
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["summary"]["container_required"] == 11
    assert "secret-token" not in stdout.getvalue()


def test_compatibility_acceptance_cli_exits_2_when_a_gate_fails() -> None:
    from interfaces.runtime import compatibility_acceptance_cli

    stdout = StringIO()

    exit_code = compatibility_acceptance_cli.run(
        [],
        stdout=stdout,
        runtime_status_provider=healthy_runtime_status,
        frontend_contract_runner=lambda: FakeSmokeResult(True, "frontend"),
        reader_actions_runner=lambda: FakeSmokeResult(False, "reader", "reader failed"),
        legacy_compat_runner=lambda: FakeSmokeResult(True, "legacy"),
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["error_message"] == "reader failed"


def test_compatibility_acceptance_cli_can_require_live_receiver() -> None:
    from interfaces.runtime import compatibility_acceptance_cli

    stdout = StringIO()
    calls: list[str] = []

    exit_code = compatibility_acceptance_cli.run(
        ["--require-live-telegram-receiver"],
        stdout=stdout,
        runtime_status_provider=healthy_runtime_status,
        frontend_contract_runner=lambda: FakeSmokeResult(True, "frontend"),
        reader_actions_runner=lambda: FakeSmokeResult(True, "reader"),
        legacy_compat_runner=lambda: FakeSmokeResult(True, "legacy"),
        live_receiver_preflight_runner=lambda: calls.append("live")
        or FakeSmokeResult(True, "live"),
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert calls == ["live"]
    assert payload["checks"][1]["name"] == "live_telegram_receiver"


def test_compatibility_acceptance_cli_fails_when_required_live_receiver_fails() -> None:
    from interfaces.runtime import compatibility_acceptance_cli

    stdout = StringIO()

    exit_code = compatibility_acceptance_cli.run(
        ["--require-live-telegram-receiver"],
        stdout=stdout,
        runtime_status_provider=healthy_runtime_status,
        frontend_contract_runner=lambda: FakeSmokeResult(True, "frontend"),
        reader_actions_runner=lambda: FakeSmokeResult(True, "reader"),
        legacy_compat_runner=lambda: FakeSmokeResult(True, "legacy"),
        live_receiver_preflight_runner=lambda: FakeSmokeResult(
            False,
            "live",
            "webhook mismatch",
        ),
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["error_message"] == "webhook mismatch"
