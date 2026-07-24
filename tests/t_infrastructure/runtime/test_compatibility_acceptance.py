from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FakeSmokeResult:
    ok: bool
    name: str
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "summary": {"name": self.name, "token": "secret-token"},
            "error_message": self.error_message,
        }


def healthy_runtime_status() -> dict[str, Any]:
    return {
        "profile": "containers",
        "ok": True,
        "counts": {"required": 11, "running": 11, "missing": 0},
        "endpoints": {
            "ok": True,
            "counts": {"required": 4, "ok": 4, "failed": 0},
        },
    }


def test_compatibility_acceptance_runs_runtime_and_all_smoke_gates() -> None:
    from infrastructure.runtime.compatibility_acceptance import (
        run_compatibility_acceptance,
    )

    calls: list[str] = []

    result = run_compatibility_acceptance(
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        runtime_status_provider=healthy_runtime_status,
        frontend_contract_runner=lambda: calls.append("frontend")
        or FakeSmokeResult(True, "frontend"),
        reader_actions_runner=lambda: calls.append("reader")
        or FakeSmokeResult(True, "reader"),
        legacy_compat_runner=lambda: calls.append("legacy")
        or FakeSmokeResult(True, "legacy"),
    )

    payload = result.to_dict()

    assert result.ok is True
    assert calls == ["frontend", "reader", "legacy"]
    assert [item["name"] for item in payload["checks"]] == [
        "container_runtime",
        "frontend_contract",
        "reader_actions",
        "legacy_compat",
    ]
    assert payload["summary"]["container_required"] == 11
    assert payload["summary"]["endpoint_required"] == 4
    assert payload["summary"]["frontend_contract"]["summary"]["name"] == "frontend"
    assert payload["summary"]["reader_actions"]["summary"]["name"] == "reader"
    assert payload["summary"]["legacy_compat"]["summary"]["name"] == "legacy"
    assert "secret-token" not in str(payload)


def test_compatibility_acceptance_skips_live_receiver_when_not_required() -> None:
    from infrastructure.runtime.compatibility_acceptance import (
        run_compatibility_acceptance,
    )

    calls: list[str] = []

    result = run_compatibility_acceptance(
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        runtime_status_provider=healthy_runtime_status,
        frontend_contract_runner=lambda: FakeSmokeResult(True, "frontend"),
        reader_actions_runner=lambda: FakeSmokeResult(True, "reader"),
        legacy_compat_runner=lambda: FakeSmokeResult(True, "legacy"),
        live_receiver_preflight_runner=lambda: calls.append("live")
        or FakeSmokeResult(False, "live", "webhook mismatch"),
    )

    assert result.ok is True
    assert calls == []
    assert [check.name for check in result.checks] == [
        "container_runtime",
        "frontend_contract",
        "reader_actions",
        "legacy_compat",
    ]


def test_compatibility_acceptance_can_require_live_receiver_preflight() -> None:
    from infrastructure.runtime.compatibility_acceptance import (
        run_compatibility_acceptance,
    )

    calls: list[str] = []

    result = run_compatibility_acceptance(
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        runtime_status_provider=healthy_runtime_status,
        frontend_contract_runner=lambda: calls.append("frontend")
        or FakeSmokeResult(True, "frontend"),
        reader_actions_runner=lambda: calls.append("reader")
        or FakeSmokeResult(True, "reader"),
        legacy_compat_runner=lambda: calls.append("legacy")
        or FakeSmokeResult(True, "legacy"),
        live_receiver_preflight_runner=lambda: calls.append("live")
        or FakeSmokeResult(True, "live"),
        require_live_telegram_receiver=True,
    )

    assert result.ok is True
    assert calls == ["live", "frontend", "reader", "legacy"]
    assert result.checks[1].name == "live_telegram_receiver"


def test_compatibility_acceptance_fails_when_required_live_receiver_mismatches() -> None:
    from infrastructure.runtime.compatibility_acceptance import (
        run_compatibility_acceptance,
    )

    calls: list[str] = []

    result = run_compatibility_acceptance(
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        runtime_status_provider=healthy_runtime_status,
        frontend_contract_runner=lambda: calls.append("frontend")
        or FakeSmokeResult(True, "frontend"),
        reader_actions_runner=lambda: calls.append("reader")
        or FakeSmokeResult(True, "reader"),
        legacy_compat_runner=lambda: calls.append("legacy")
        or FakeSmokeResult(True, "legacy"),
        live_receiver_preflight_runner=lambda: calls.append("live")
        or FakeSmokeResult(False, "live", "webhook mismatch"),
        require_live_telegram_receiver=True,
    )

    assert result.ok is False
    assert calls == ["live"]
    assert result.error_message == "webhook mismatch"
    assert result.checks[-1].name == "live_telegram_receiver"
    assert result.checks[-1].ok is False


def test_compatibility_acceptance_stops_when_runtime_is_not_ready() -> None:
    from infrastructure.runtime.compatibility_acceptance import (
        run_compatibility_acceptance,
    )

    calls: list[str] = []

    result = run_compatibility_acceptance(
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        runtime_status_provider=lambda: {
            **healthy_runtime_status(),
            "ok": False,
            "counts": {"required": 11, "running": 10, "missing": 1},
        },
        frontend_contract_runner=lambda: calls.append("frontend")
        or FakeSmokeResult(True, "frontend"),
        reader_actions_runner=lambda: calls.append("reader")
        or FakeSmokeResult(True, "reader"),
        legacy_compat_runner=lambda: calls.append("legacy")
        or FakeSmokeResult(True, "legacy"),
    )

    assert result.ok is False
    assert calls == []
    assert result.error_message == "container runtime is not ready"
    assert result.checks[-1].name == "container_runtime"
    assert result.checks[-1].ok is False


def test_compatibility_acceptance_stops_when_reader_actions_fail() -> None:
    from infrastructure.runtime.compatibility_acceptance import (
        run_compatibility_acceptance,
    )

    calls: list[str] = []

    result = run_compatibility_acceptance(
        api_root="https://lang-reader-server.ngrok.app/api/v1",
        runtime_status_provider=healthy_runtime_status,
        frontend_contract_runner=lambda: calls.append("frontend")
        or FakeSmokeResult(True, "frontend"),
        reader_actions_runner=lambda: calls.append("reader")
        or FakeSmokeResult(False, "reader", "reader actions failed"),
        legacy_compat_runner=lambda: calls.append("legacy")
        or FakeSmokeResult(True, "legacy"),
    )

    assert result.ok is False
    assert calls == ["frontend", "reader"]
    assert result.error_message == "reader actions failed"
    assert result.checks[-1].name == "reader_actions"
    assert result.checks[-1].ok is False
