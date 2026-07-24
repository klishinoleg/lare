from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TextIO

from core.config import settings
from infrastructure.runtime.compatibility_acceptance import (
    RuntimeStatusProvider,
    SmokeRunner,
    run_compatibility_acceptance,
)
from infrastructure.runtime.frontend_contract_smoke import (
    run_frontend_contract_smoke,
)
from infrastructure.runtime.legacy_compat_smoke import (
    UrllibJsonHttpClient,
    run_legacy_compat_smoke,
)
from infrastructure.runtime.local_supervisor import (
    ContainerRuntimeSupervisor,
    LocalRuntimeSupervisor,
    check_runtime_endpoint,
    collect_container_snapshots,
    collect_process_snapshots,
    evaluate_endpoints,
)
from infrastructure.runtime.reader_actions_smoke import (
    UrllibUploadFetcher,
    run_reader_actions_smoke,
)
from infrastructure.runtime.telegram_receiver_preflight import (
    TelegramReceiverPreflightConfig,
    TelegramReceiverPreflightResult,
    run_telegram_receiver_preflight,
)
from interfaces.runtime.telegram_receiver_preflight_cli import (
    DEFAULT_DESIRED_WEBHOOK_URL,
)


Sleep = Callable[[float], object]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Lazy Reader full old-frontend compatibility acceptance gate.",
    )
    parser.add_argument(
        "--api-root",
        default="https://lang-reader-server.ngrok.app/api/v1",
        help="API root with /api/v1 prefix.",
    )
    parser.add_argument(
        "--server-root",
        default="https://lang-reader-server.ngrok.app",
        help="Server root used to fetch /uploads files when enabled.",
    )
    parser.add_argument(
        "--tg-user-id-base",
        type=int,
        default=None,
        help="Optional base for synthetic Telegram ids. Three offsets are used.",
    )
    parser.add_argument(
        "--seed",
        default=None,
        help="Stable suffix for generated names.",
    )
    parser.add_argument(
        "--chapter-ready-attempts",
        type=int,
        default=80,
        help="How many times to poll chapter readiness in each smoke.",
    )
    parser.add_argument(
        "--chapter-ready-delay-seconds",
        type=float,
        default=1.5,
        help="Delay between chapter readiness polls.",
    )
    parser.add_argument(
        "--check-upload-files",
        action="store_true",
        help="Fetch generated reader-action voice files and verify byte size.",
    )
    parser.add_argument(
        "--require-live-telegram-receiver",
        action="store_true",
        help="Fail unless Telegram getWebhookInfo points at the expected receiver.",
    )
    parser.add_argument(
        "--desired-webhook-url",
        default=DEFAULT_DESIRED_WEBHOOK_URL,
        help="Expected Telegram webhook URL when live receiver preflight is required.",
    )
    parser.add_argument(
        "--bot-api-base-url",
        default="https://api.telegram.org",
        help="Telegram Bot API base URL for live receiver preflight.",
    )
    return parser


def run(
    argv: list[str] | None = None,
    stdout: TextIO = sys.stdout,
    runtime_status_provider: RuntimeStatusProvider | None = None,
    frontend_contract_runner: SmokeRunner | None = None,
    reader_actions_runner: SmokeRunner | None = None,
    legacy_compat_runner: SmokeRunner | None = None,
    live_receiver_preflight_runner: SmokeRunner | None = None,
    sleep: Sleep | None = None,
) -> int:
    args = _parser().parse_args(argv)
    effective_sleep = sleep or __import__("time").sleep
    tg_base = args.tg_user_id_base or 936000000 + random.randint(0, 999999)
    seed = args.seed or str(tg_base)

    frontend_runner = frontend_contract_runner or _frontend_runner(
        api_root=args.api_root,
        tg_user_id=tg_base + 1,
        seed=f"{seed}-frontend",
        chapter_ready_attempts=args.chapter_ready_attempts,
        chapter_ready_delay_seconds=args.chapter_ready_delay_seconds,
        sleep=effective_sleep,
    )
    reader_runner = reader_actions_runner or _reader_actions_runner(
        api_root=args.api_root,
        server_root=args.server_root,
        tg_user_id=tg_base + 2,
        seed=f"{seed}-reader",
        chapter_ready_attempts=args.chapter_ready_attempts,
        chapter_ready_delay_seconds=args.chapter_ready_delay_seconds,
        check_upload_files=args.check_upload_files,
        sleep=effective_sleep,
    )
    legacy_runner = legacy_compat_runner or _legacy_runner(
        api_root=args.api_root,
        tg_user_id=tg_base + 3,
        seed=f"{seed}-legacy",
        chapter_ready_attempts=args.chapter_ready_attempts,
        chapter_ready_delay_seconds=args.chapter_ready_delay_seconds,
        sleep=effective_sleep,
    )
    live_runner = live_receiver_preflight_runner or _live_receiver_preflight_runner(
        desired_webhook_url=args.desired_webhook_url,
        bot_api_base_url=args.bot_api_base_url,
    )

    result = run_compatibility_acceptance(
        api_root=args.api_root,
        runtime_status_provider=runtime_status_provider or _container_status_provider,
        frontend_contract_runner=frontend_runner,
        reader_actions_runner=reader_runner,
        legacy_compat_runner=legacy_runner,
        live_receiver_preflight_runner=live_runner,
        require_live_telegram_receiver=args.require_live_telegram_receiver,
    )
    stdout.write(json.dumps(result.to_dict(), ensure_ascii=False))
    stdout.write("\n")
    return 0 if result.ok else 2


def _container_status_provider() -> dict[str, object]:
    supervisor = ContainerRuntimeSupervisor.default()
    status = supervisor.evaluate(
        containers=collect_container_snapshots(),
        processes=collect_process_snapshots(),
    )
    endpoint_status = evaluate_endpoints(
        LocalRuntimeSupervisor.default_endpoint_specs(),
        check_runtime_endpoint,
    )
    return {
        "profile": "containers",
        **status.to_dict(),
        "endpoints": endpoint_status.to_dict(),
        "ok": status.ok and endpoint_status.ok,
    }


def _frontend_runner(
    *,
    api_root: str,
    tg_user_id: int,
    seed: str,
    chapter_ready_attempts: int,
    chapter_ready_delay_seconds: float,
    sleep: Sleep,
) -> SmokeRunner:
    return lambda: run_frontend_contract_smoke(
        client=UrllibJsonHttpClient(api_root.rstrip("/")),
        api_root=api_root,
        tg_user_id=tg_user_id,
        seed=seed,
        chapter_ready_attempts=chapter_ready_attempts,
        chapter_ready_delay_seconds=chapter_ready_delay_seconds,
        sleep=sleep,
    )


def _reader_actions_runner(
    *,
    api_root: str,
    server_root: str,
    tg_user_id: int,
    seed: str,
    chapter_ready_attempts: int,
    chapter_ready_delay_seconds: float,
    check_upload_files: bool,
    sleep: Sleep,
) -> SmokeRunner:
    return lambda: run_reader_actions_smoke(
        client=UrllibJsonHttpClient(api_root.rstrip("/")),
        api_root=api_root,
        tg_user_id=tg_user_id,
        seed=seed,
        chapter_ready_attempts=chapter_ready_attempts,
        chapter_ready_delay_seconds=chapter_ready_delay_seconds,
        sleep=sleep,
        check_upload_files=check_upload_files,
        upload_fetcher=UrllibUploadFetcher(server_root) if check_upload_files else None,
    )


def _legacy_runner(
    *,
    api_root: str,
    tg_user_id: int,
    seed: str,
    chapter_ready_attempts: int,
    chapter_ready_delay_seconds: float,
    sleep: Sleep,
) -> SmokeRunner:
    return lambda: run_legacy_compat_smoke(
        client=UrllibJsonHttpClient(api_root.rstrip("/")),
        api_root=api_root,
        tg_user_id=tg_user_id,
        seed=seed,
        chapter_ready_attempts=chapter_ready_attempts,
        chapter_ready_delay_seconds=chapter_ready_delay_seconds,
        sleep=sleep,
    )


@dataclass(frozen=True)
class _TelegramReceiverPreflightSmokeResult:
    result: TelegramReceiverPreflightResult

    @property
    def ok(self) -> bool:
        return self.result.ok

    @property
    def error_message(self) -> str | None:
        if self.result.ok:
            return None
        if self.result.issues:
            return ", ".join(self.result.issues)
        return "live Telegram receiver preflight failed"

    def to_dict(self) -> dict[str, Any]:
        return self.result.to_dict()


def _live_receiver_preflight_runner(
    *,
    desired_webhook_url: str,
    bot_api_base_url: str,
) -> SmokeRunner:
    def run_preflight() -> _TelegramReceiverPreflightSmokeResult:
        result = asyncio.run(
            run_telegram_receiver_preflight(
                TelegramReceiverPreflightConfig(
                    token=settings.tg_bot_token or "",
                    desired_webhook_url=desired_webhook_url,
                    bot_api_base_url=bot_api_base_url,
                ),
            ),
        )
        return _TelegramReceiverPreflightSmokeResult(result)

    return run_preflight


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
