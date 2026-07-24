from __future__ import annotations

from decimal import Decimal

import pytest

from application.events.event_types import FinanceEventTypes, SegmentEvents
from application.events.handlers_register.finance import register_finance_main_brokers
from application.events.handlers_register.segment import register_segment_brokers
from application.text.segment.dtos import CreateSegmentByWordChapterIndexesDTO
from application.text.segment.utils.segment_factory import publish_segment_create_request_event
from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from domain.account.entities import AccountEntity
from domain.ai.entities import AiModelEntity
from domain.finance.enums.account_usage_type import AccountUsageType
from domain.finance.enums.transaction_type import TransactionType
from domain.text_data.enums import TextActionsTypes, TextTranslateTypes
from infrastructure.broker.mock.broker import MockEventBroker
from infrastructure.broker.mock.publisher import MockPublisher
from infrastructure.repository.tortoise.models import (
    AccountModel,
    AccountTransactionModel,
    AccountUsageModel,
    AiLogModel,
    AiModelModel,
    BookModel,
    ChapterModel,
    LanguageModel,
    SegmentModel,
    SegmentTranslateModel,
    WordChapterModel,
    WordModel,
)


@pytest.mark.asyncio
async def test_segment_create_event_chain_saves_projection_and_usage(tmp_path) -> None:
    db_path = tmp_path / "segment-chain.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"
    MockPublisher.clear_events()
    MockEventBroker.subscribers.clear()

    await init_tortoise()
    try:
        register_finance_main_brokers(EventBrokerTypes.MOCK)
        register_segment_brokers(EventBrokerTypes.MOCK)

        language = await LanguageModel.create(
            name="English",
            slug="en",
            code="en",
            original_name="English",
            ordering=1,
        )
        account = await AccountModel.create(username="segment-user", credits=0)
        book = await BookModel.create(
            name="Segment Book",
            language_id=language.id,
            account_id=account.id,
            image="",
        )
        chapter = await ChapterModel.create(
            name="Chapter 1",
            book_id=book.id,
            account_id=account.id,
            source_url="",
            position=0,
            is_ready=True,
        )
        words = [
            await WordModel.create(name="hello", language_id=language.id),
            await WordModel.create(name="brave", language_id=language.id),
            await WordModel.create(name="world", language_id=language.id),
        ]
        word_chapters = []
        for position, word in enumerate(words):
            word_chapters.append(
                await WordChapterModel.create(
                    name=word.name,
                    word_id=word.id,
                    chapter_id=chapter.id,
                    position=position,
                    n=0,
                )
            )

        await publish_segment_create_request_event(
            create_dto=CreateSegmentByWordChapterIndexesDTO(
                indexes=[item.id for item in word_chapters],
                a=TextActionsTypes.TRANSLATE,
                translate_type=TextTranslateTypes.TEXT,
            ),
            account=AccountEntity(
                id=account.id,
                username=account.username,
                public_name=account.public_name,
                email=account.email,
                credits=Decimal("0"),
            ),
            ai_model_entity=AiModelEntity(
                name="Local test model",
                model="local-test",
                input_cost=Decimal("0"),
                output_cost=Decimal("0"),
                allow_to=[AccountUsageType.AI_TRANSLATE],
            ),
        )

        segment = await SegmentModel.get()
        translate = await SegmentTranslateModel.get(segment_id=segment.id)
        usage = await AccountUsageModel.get(usage_id=segment.id)
        transaction = await AccountTransactionModel.get(usage_id=usage.id)
        ai_log = await AiLogModel.get()
        ai_model = await AiModelModel.get()
        linked_words = await WordChapterModel.filter(segment_id=segment.id).order_by("position")
        events = MockPublisher.get_events()
        event_types = [event_type for event_type, _ in events]
        ai_events = [
            event
            for event_type, event in events
            if event_type
            in {
                SegmentEvents.SEGMENT_AI_REQUESTED,
                SegmentEvents.SEGMENT_AI_PROCESSING,
                SegmentEvents.SEGMENT_AI_RECEIVED,
                SegmentEvents.SEGMENT_AI_SAVED,
            }
        ]

        assert segment.name == "hello brave world"
        assert translate.translate == "[local] hello brave world"
        assert ai_model.model == "local-test"
        assert ai_log.ai_model_id == ai_model.id
        assert ai_log.ai_request == "hello brave world"
        assert ai_log.ai_response == "[local] hello brave world"
        assert ai_log.hash_str
        assert [event.ai_log_id for event in ai_events] == [ai_log.id] * 4
        assert usage.usage_type == AccountUsageType.AI_TRANSLATE
        assert usage.usage_amount == 3
        assert transaction.transaction_type == TransactionType.AI_USAGE
        assert transaction.credits_amount == Decimal("-3.00")
        assert [item.id for item in linked_words] == [item.id for item in word_chapters]
        assert SegmentEvents.SEGMENT_CREATE_REQUESTED in event_types
        assert SegmentEvents.SEGMENT_AI_SAVED in event_types
        assert FinanceEventTypes.USAGE_CREATED in event_types
        assert FinanceEventTypes.TRANSACTION_CREATED in event_types
    finally:
        await close_tortoise()
