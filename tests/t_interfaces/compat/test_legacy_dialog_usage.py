from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from application.ai.reader_provider import ReaderAiProviderResponse, set_reader_ai_provider
from application.events.handlers_register.finance import register_finance_main_brokers
from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from domain.finance.enums.account_usage_type import AccountUsageType
from domain.finance.enums.transaction_type import TransactionType
from infrastructure.broker.mock.broker import MockEventBroker
from infrastructure.broker.mock.publisher import MockPublisher
from infrastructure.repository.tortoise.models import (
    AccountModel,
    AccountTransactionModel,
    AccountUsageModel,
    BookModel,
    ChapterModel,
    CompatTextPartModel,
    LanguageModel,
)


@pytest.mark.asyncio
async def test_legacy_text_part_dialog_charges_ai_dialog_usage(tmp_path) -> None:
    db_path = tmp_path / "legacy-dialog-usage.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    settings.languages = "en|ru"
    MockPublisher.clear_events()
    MockEventBroker.subscribers.clear()

    class FakeReaderAiProvider:
        async def answer_dialog(self, request: object) -> ReaderAiProviderResponse:
            return ReaderAiProviderResponse(content="provider dialog answer", provider="fixture")

    set_reader_ai_provider(FakeReaderAiProvider())
    from interfaces.fast_api.main import app

    await init_tortoise()
    try:
        register_finance_main_brokers(EventBrokerTypes.MOCK, bills=False)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            auth_response = await client.post(
                "/api/v1/account/telegram_auth/",
                json={
                    "auth_data": {
                        "user": {
                            "id": 9102001,
                            "username": "dialog_usage",
                            "first_name": "Dialog",
                            "last_name": "Usage",
                            "language_code": "en",
                        }
                    }
                },
            )
            assert auth_response.status_code == 200
            auth_data = auth_response.json()
            account_id = auth_data["account"]["id"]
            headers = {"Authorization": f"Token {auth_data['token']}"}
            await AccountTransactionModel.create(
                account_id=account_id,
                transaction_type=TransactionType.MANUAL,
                credits_amount=Decimal("5.00"),
            )
            await AccountModel.filter(id=account_id).update(credits=Decimal("5.00"))

            language = await LanguageModel.get(code="en")
            book = await BookModel.create(
                name="Dialog usage book",
                account_id=account_id,
                language_id=language.id,
                image="",
            )
            chapter = await ChapterModel.create(
                name="Dialog usage chapter",
                account_id=account_id,
                book_id=book.id,
                source_url="",
                position=0,
                is_ready=True,
            )
            text_part = await CompatTextPartModel.create(
                account_id=account_id,
                chapter_id=chapter.id,
                language_id=language.id,
                name="hello brave world",
                translate="[local] hello brave world",
                transliteration="hello brave world",
            )

            response = await client.post(
                f"/api/v1/text_part/{text_part.id}/dialog/",
                headers=headers,
                json={"message": "Explain this sentence"},
            )

        assert response.status_code == 200
        dialog = response.json()["dialog"]
        assert [item["role"] for item in dialog] == ["user", "assistant"]
        assert dialog[-1]["content"] == "provider dialog answer"

        usage = await AccountUsageModel.get(
            account_id=account_id,
            usage_type=AccountUsageType.AI_DIALOG,
        )
        transaction = await AccountTransactionModel.get(usage_id=usage.id)
        account = await AccountModel.get(id=account_id)

        assert usage.usage_id == text_part.id
        assert usage.usage_amount == 1
        assert usage.credits_amount == Decimal("5.00")
        assert transaction.transaction_type == TransactionType.AI_USAGE
        assert transaction.credits_amount == Decimal("-5.00")
        assert account.credits == Decimal("0.00")
    finally:
        set_reader_ai_provider(None)
        await close_tortoise()
