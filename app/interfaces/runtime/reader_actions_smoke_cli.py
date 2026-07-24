from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from typing import TextIO

from infrastructure.runtime.legacy_compat_smoke import (
    JsonHttpClient,
    UrllibJsonHttpClient,
)
from infrastructure.runtime.reader_actions_smoke import (
    UploadFetcher,
    UrllibUploadFetcher,
    run_reader_actions_smoke,
)


ClientFactory = Callable[[str], JsonHttpClient]
Sleep = Callable[[float], object]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Lazy Reader paid reader actions compatibility smoke.",
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
        "--tg-user-id",
        type=int,
        default=None,
        help="Synthetic Telegram user id. Defaults to a random reader-actions id.",
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
    parser.add_argument(
        "--check-upload-files",
        action="store_true",
        help="Fetch generated voice upload files and verify byte size.",
    )
    return parser


def run(
    argv: list[str] | None = None,
    stdout: TextIO = sys.stdout,
    client_factory: ClientFactory = UrllibJsonHttpClient,
    sleep: Sleep | None = None,
    upload_fetcher: UploadFetcher | None = None,
) -> int:
    args = _parser().parse_args(argv)
    fetcher = upload_fetcher
    if args.check_upload_files and fetcher is None:
        fetcher = UrllibUploadFetcher(args.server_root)
    result = run_reader_actions_smoke(
        client=client_factory(args.api_root.rstrip("/")),
        api_root=args.api_root,
        tg_user_id=args.tg_user_id,
        seed=args.seed,
        chapter_ready_attempts=args.chapter_ready_attempts,
        chapter_ready_delay_seconds=args.chapter_ready_delay_seconds,
        sleep=sleep or __import__("time").sleep,
        check_upload_files=args.check_upload_files,
        upload_fetcher=fetcher,
    )
    stdout.write(json.dumps(result.to_dict(), ensure_ascii=False))
    stdout.write("\n")
    return 0 if result.ok else 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
