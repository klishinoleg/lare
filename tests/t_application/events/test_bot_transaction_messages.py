from __future__ import annotations

from decimal import Decimal

import pytest

from application.events.event_handlers.bot import transaction_created, transaction_error
from application.events.event_handlers.bot.transaction_created import (
    TransactionCreatedEventHandler,
)
from application.events.event_handlers.bot.transaction_error import TransactionErrorEventHandler
from application.events.event_types import FinanceEventTypes
from application.finance.events import TransactionCreatedEvent, TransactionErrorEvent
from domain.finance.enums.transaction_type import TransactionType


class FailingAccountService:
    async def get_by_id(self, account_id: int) -> object:
        raise AssertionError("empty bot messages must not load accounts")


class FailingBotFactory:
    async def get(self, account_entity: object) -> object:
        raise AssertionError("empty bot messages must not resolve bots")


@pytest.mark.asyncio
async def test_ai_usage_transaction_does_not_send_empty_bot_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        transaction_created,
        "AccountService",
        lambda: FailingAccountService(),
    )
    monkeypatch.setattr(transaction_created, "DIBot", FailingBotFactory())

    await TransactionCreatedEventHandler.handler(
        TransactionCreatedEvent(
            account_id=1,
            transaction_type=TransactionType.AI_USAGE,
            credits_amount=Decimal("1"),
        )
    )


@pytest.mark.asyncio
async def test_empty_transaction_error_does_not_send_empty_bot_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        transaction_error,
        "AccountService",
        lambda: FailingAccountService(),
    )
    monkeypatch.setattr(transaction_error, "DIBot", FailingBotFactory())

    await TransactionErrorEventHandler.handler(
        TransactionErrorEvent(
            account_id=1,
            step=FinanceEventTypes.TRANSACTION_CREATED,
            error_message="",
        )
    )
