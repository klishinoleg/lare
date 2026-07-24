from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from typing import TextIO

from core.db import close_tortoise, init_tortoise
from infrastructure.broker.event_outbox import (
    OUTBOX_STATUS_DEAD_LETTERED,
    OUTBOX_STATUS_FAILED,
)
from infrastructure.broker.event_outbox_operations import EventOutboxOperations


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and replay event outbox rows.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List failed/dead-lettered outbox rows.")
    list_parser.add_argument("--limit", type=int, default=50)
    list_parser.add_argument(
        "--status",
        action="append",
        choices=[OUTBOX_STATUS_DEAD_LETTERED, OUTBOX_STATUS_FAILED],
        help="Filter status. Can be passed more than once.",
    )

    replay_parser = subparsers.add_parser("replay", help="Republish one saved outbox event.")
    replay_parser.add_argument("id", type=int)

    return parser


async def run(argv: list[str] | None = None, stdout: TextIO = sys.stdout) -> int:
    args = _parser().parse_args(argv)
    operations = EventOutboxOperations()

    if args.command == "list":
        statuses = tuple(args.status) if args.status else (OUTBOX_STATUS_DEAD_LETTERED, OUTBOX_STATUS_FAILED)
        items = await operations.list_failed(limit=args.limit, statuses=statuses)
        stdout.write(
            json.dumps(
                {"count": len(items), "items": [asdict(item) for item in items]},
                ensure_ascii=False,
            )
        )
        stdout.write("\n")
        return 0

    if args.command == "replay":
        item = await operations.replay(args.id)
        stdout.write(json.dumps(asdict(item), ensure_ascii=False))
        stdout.write("\n")
        return 0

    raise ValueError(f"Unsupported command: {args.command}")


async def _main(argv: list[str] | None = None, stdout: TextIO = sys.stdout) -> int:
    await init_tortoise()
    try:
        return await run(argv, stdout)
    finally:
        await close_tortoise()


def main() -> None:
    raise SystemExit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
