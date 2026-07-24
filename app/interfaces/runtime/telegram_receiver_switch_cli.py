from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Callable
from typing import TextIO

from core.config import settings
from infrastructure.runtime.telegram_receiver_preflight import ApiFactory
from infrastructure.runtime.telegram_receiver_switch import (
    TelegramReceiverSwitchConfig,
    run_telegram_receiver_switch,
)
from interfaces.runtime.telegram_receiver_preflight_cli import (
    DEFAULT_DESIRED_WEBHOOK_URL,
)


TokenProvider = Callable[[], str]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan or explicitly apply Lazy Reader Telegram webhook switch.",
    )
    parser.add_argument(
        "--desired-webhook-url",
        default=DEFAULT_DESIRED_WEBHOOK_URL,
        help="Webhook URL to set after explicit confirmation.",
    )
    parser.add_argument(
        "--bot-api-base-url",
        default="https://api.telegram.org",
        help="Telegram Bot API base URL.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Request setWebhook. Requires --confirm-receiver-switch.",
    )
    parser.add_argument(
        "--confirm-receiver-switch",
        action="store_true",
        help="Confirm that receiver ownership may be changed.",
    )
    parser.add_argument(
        "--drop-pending-updates",
        action="store_true",
        help="Pass drop_pending_updates=true to setWebhook.",
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
    result = await run_telegram_receiver_switch(
        TelegramReceiverSwitchConfig(
            token=token_provider(),
            desired_webhook_url=args.desired_webhook_url,
            bot_api_base_url=args.bot_api_base_url,
            apply=args.apply,
            confirm_receiver_switch=args.confirm_receiver_switch,
            drop_pending_updates=args.drop_pending_updates,
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
