from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from typing import Any, Protocol


class SmokeResultLike(Protocol):
    ok: bool
    error_message: str | None

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError


RuntimeStatusProvider = Callable[[], dict[str, Any]]
SmokeRunner = Callable[[], SmokeResultLike]


@dataclass(frozen=True)
class AcceptanceCheck:
    name: str
    ok: bool
    error_message: str | None = None


@dataclass(frozen=True)
class CompatibilityAcceptanceResult:
    ok: bool
    api_root: str
    checks: tuple[AcceptanceCheck, ...]
    summary: dict[str, Any]
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "api_root": self.api_root,
            "checks": [asdict(check) for check in self.checks],
            "summary": _redact_secret_values(self.summary),
            "error_message": self.error_message,
        }


def run_compatibility_acceptance(
    *,
    api_root: str,
    runtime_status_provider: RuntimeStatusProvider,
    frontend_contract_runner: SmokeRunner,
    reader_actions_runner: SmokeRunner,
    legacy_compat_runner: SmokeRunner,
    live_receiver_preflight_runner: SmokeRunner | None = None,
    require_live_telegram_receiver: bool = False,
) -> CompatibilityAcceptanceResult:
    checks: list[AcceptanceCheck] = []
    summary: dict[str, Any] = {}

    runtime_status = runtime_status_provider()
    runtime_check = _runtime_check(runtime_status)
    checks.append(runtime_check)
    summary.update(_runtime_summary(runtime_status))
    if not runtime_check.ok:
        return CompatibilityAcceptanceResult(
            ok=False,
            api_root=api_root.rstrip("/"),
            checks=tuple(checks),
            summary=summary,
            error_message=runtime_check.error_message,
        )

    if require_live_telegram_receiver:
        if live_receiver_preflight_runner is None:
            return CompatibilityAcceptanceResult(
                ok=False,
                api_root=api_root.rstrip("/"),
                checks=(
                    *checks,
                    AcceptanceCheck(
                        name="live_telegram_receiver",
                        ok=False,
                        error_message="live Telegram receiver preflight runner is required",
                    ),
                ),
                summary=summary,
                error_message="live Telegram receiver preflight runner is required",
            )

        result = live_receiver_preflight_runner()
        summary["live_telegram_receiver"] = result.to_dict()
        check = AcceptanceCheck(
            name="live_telegram_receiver",
            ok=bool(result.ok),
            error_message=None
            if result.ok
            else result.error_message or "live_telegram_receiver failed",
        )
        checks.append(check)
        if not check.ok:
            return CompatibilityAcceptanceResult(
                ok=False,
                api_root=api_root.rstrip("/"),
                checks=tuple(checks),
                summary=summary,
                error_message=check.error_message,
            )

    for check_name, summary_key, runner in (
        ("frontend_contract", "frontend_contract", frontend_contract_runner),
        ("reader_actions", "reader_actions", reader_actions_runner),
        ("legacy_compat", "legacy_compat", legacy_compat_runner),
    ):
        result = runner()
        result_dict = result.to_dict()
        summary[summary_key] = result_dict
        check = AcceptanceCheck(
            name=check_name,
            ok=bool(result.ok),
            error_message=None if result.ok else result.error_message or f"{check_name} failed",
        )
        checks.append(check)
        if not check.ok:
            return CompatibilityAcceptanceResult(
                ok=False,
                api_root=api_root.rstrip("/"),
                checks=tuple(checks),
                summary=summary,
                error_message=check.error_message,
            )

    return CompatibilityAcceptanceResult(
        ok=True,
        api_root=api_root.rstrip("/"),
        checks=tuple(checks),
        summary=summary,
    )


def _runtime_check(runtime_status: Mapping[str, Any]) -> AcceptanceCheck:
    if runtime_status.get("ok") is True:
        return AcceptanceCheck(name="container_runtime", ok=True)
    return AcceptanceCheck(
        name="container_runtime",
        ok=False,
        error_message="container runtime is not ready",
    )


def _runtime_summary(runtime_status: Mapping[str, Any]) -> dict[str, Any]:
    counts = runtime_status.get("counts") if isinstance(runtime_status, Mapping) else {}
    endpoints = runtime_status.get("endpoints") if isinstance(runtime_status, Mapping) else {}
    endpoint_counts = {}
    if isinstance(endpoints, Mapping):
        endpoint_counts = endpoints.get("counts") or {}
    return {
        "profile": runtime_status.get("profile"),
        "container_required": _safe_int(counts.get("required") if isinstance(counts, Mapping) else 0),
        "container_running": _safe_int(counts.get("running") if isinstance(counts, Mapping) else 0),
        "container_missing": _safe_int(counts.get("missing") if isinstance(counts, Mapping) else 0),
        "endpoint_required": _safe_int(
            endpoint_counts.get("required") if isinstance(endpoint_counts, Mapping) else 0,
        ),
        "endpoint_ok": _safe_int(endpoint_counts.get("ok") if isinstance(endpoint_counts, Mapping) else 0),
        "endpoint_failed": _safe_int(
            endpoint_counts.get("failed") if isinstance(endpoint_counts, Mapping) else 0,
        ),
        "runtime_status": runtime_status,
    }


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _redact_secret_values(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(secret in key_text for secret in ("token", "secret", "password", "api_key")):
                result[str(key)] = "<redacted>"
            else:
                result[str(key)] = _redact_secret_values(item)
        return result
    if isinstance(value, list):
        return [_redact_secret_values(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_secret_values(item) for item in value]
    return value
