from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Callable
from typing import TextIO

from core.config import settings
from infrastructure.runtime.telegram_receiver_preflight import (
    ApiFactory,
    TelegramReceiverPreflightConfig,
    run_telegram_receiver_preflight,
)


TokenProvider = Callable[[], str]


DEFAULT_DESIRED_WEBHOOK_URL = "https://lang-reader-server.ngrok.app/api/v1/telegram/update/"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely inspect Telegram receiver ownership for Lazy Reader.",
    )
    parser.add_argument(
        "--desired-webhook-url",
        default=DEFAULT_DESIRED_WEBHOOK_URL,
        help="Expected webhook URL for the current local/ngrok receiver.",
    )
    parser.add_argument(
        "--bot-api-base-url",
        default="https://api.telegram.org",
        help="Telegram Bot API base URL.",
    )
    return parser


def _default_token_provider() -> str:
    return settings.tg_bot_token or ""


async def run(
    argv: list[str] | None = None,
    stdout: TextIO = sys.stdout,
    token_provider: TokenProvider = _default_token_provider,
    api_factory: ApiFactory | None = None,
) -> int:
    args = _parser().parse_args(argv)
    result = await run_telegram_receiver_preflight(
        TelegramReceiverPreflightConfig(
            token=token_provider(),
            desired_webhook_url=args.desired_webhook_url,
            bot_api_base_url=args.bot_api_base_url,
        ),
        api_factory=api_factory,
    )
    stdout.write(json.dumps(result.to_dict(), ensure_ascii=False))
    stdout.write("\n")
    return 0 if result.ok else 2


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
