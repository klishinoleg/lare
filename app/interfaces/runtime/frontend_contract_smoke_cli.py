from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from typing import TextIO

from infrastructure.runtime.frontend_contract_smoke import (
    run_frontend_contract_smoke,
)
from infrastructure.runtime.legacy_compat_smoke import (
    JsonHttpClient,
    UrllibJsonHttpClient,
)


ClientFactory = Callable[[str], JsonHttpClient]
Sleep = Callable[[float], object]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Lazy Reader old React reducer API compatibility smoke.",
    )
    parser.add_argument(
        "--api-root",
        default="https://lang-reader-server.ngrok.app/api/v1",
        help="API root with /api/v1 prefix.",
    )
    parser.add_argument(
        "--tg-user-id",
        type=int,
        default=None,
        help="Synthetic Telegram user id. Defaults to a random contract id.",
    )
    parser.add_argument(
        "--seed",
        default=None,
        help="Stable suffix for generated names.",
    )
    parser.add_argument(
        "--chapter-ready-attempts",
        type=int,
        default=70,
        help="How many times to poll chapter readiness.",
    )
    parser.add_argument(
        "--chapter-ready-delay-seconds",
        type=float,
        default=1.5,
        help="Delay between chapter readiness polls.",
    )
    return parser


def run(
    argv: list[str] | None = None,
    stdout: TextIO = sys.stdout,
    client_factory: ClientFactory = UrllibJsonHttpClient,
    sleep: Sleep | None = None,
) -> int:
    args = _parser().parse_args(argv)
    client = client_factory(args.api_root.rstrip("/"))
    result = run_frontend_contract_smoke(
        client=client,
        api_root=args.api_root,
        tg_user_id=args.tg_user_id,
        seed=args.seed,
        chapter_ready_attempts=args.chapter_ready_attempts,
        chapter_ready_delay_seconds=args.chapter_ready_delay_seconds,
        sleep=sleep or __import__("time").sleep,
    )
    stdout.write(json.dumps(result.to_dict(), ensure_ascii=False))
    stdout.write("\n")
    return 0 if result.ok else 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
