from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Callable
from typing import TextIO

from application.ai.reader_provider import ReaderAiProvider, get_reader_ai_provider
from infrastructure.ai.provider_bootstrap import configure_reader_ai_provider
from infrastructure.ai.reader_provider_smoke import run_reader_provider_smoke


ProviderFactory = Callable[[], ReaderAiProvider]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a safe Lazy Reader AI provider smoke test.",
    )
    parser.add_argument(
        "--include-media",
        action="store_true",
        help="Also run voice and image provider checks.",
    )
    parser.add_argument(
        "--require-external",
        action="store_true",
        help="Fail unless every smoke step is served by the OpenAI-compatible provider.",
    )
    parser.add_argument(
        "--require-provider",
        help="Fail unless every smoke step is served by the named provider.",
    )
    return parser


def _default_provider_factory() -> ReaderAiProvider:
    configure_reader_ai_provider()
    return get_reader_ai_provider()


async def run(
    argv: list[str] | None = None,
    stdout: TextIO = sys.stdout,
    provider_factory: ProviderFactory = _default_provider_factory,
) -> int:
    args = _parser().parse_args(argv)
    result = await run_reader_provider_smoke(
        provider_factory(),
        include_media=args.include_media,
        required_provider=args.require_provider or ("openai" if args.require_external else None),
    )
    stdout.write(json.dumps(result.to_dict(), ensure_ascii=False))
    stdout.write("\n")
    return 0 if result.ok else 2


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
