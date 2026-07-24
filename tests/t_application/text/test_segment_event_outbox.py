from __future__ import annotations

from decimal import Decimal

import pytest

from application.events.event_types import SegmentEvents
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
from domain.text_data.enums import TextActionsTypes, TextTranslateTypes
from infrastructure.broker.mock.broker import MockEventBroker
from infrastructure.broker.mock.publisher import MockPublisher
from infrastructure.repository.tortoise.models import (
    AccountModel,
    BookModel,
    ChapterModel,
    EventOutboxModel,
    LanguageModel,
    WordChapterModel,
    WordModel,
)


@pytest.mark.asyncio
async def test_segment_event_chain_records_processed_outbox_states(tmp_path) -> None:
    db_path = tmp_path / "segment-outbox.sqlite3"
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
        account = await AccountModel.create(username="segment-outbox-user", credits=0)
        book = await BookModel.create(
            name="Segment Outbox Book",
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
            await WordModel.create(name="durable", language_id=language.id),
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
            pid="segment:outbox-pid",
        )

        outbox_events = await EventOutboxModel.filter(
            pid="segment:outbox-pid",
            event_type__startswith="segment.",
        ).order_by("id")

        event_types = [item.event_type for item in outbox_events]
        assert event_types == [
            SegmentEvents.SEGMENT_CREATE_REQUESTED.value,
            SegmentEvents.SEGMENT_CREATED.value,
            SegmentEvents.SEGMENT_AI_REQUESTED.value,
            SegmentEvents.SEGMENT_AI_PROCESSING.value,
            SegmentEvents.SEGMENT_AI_RECEIVED.value,
            SegmentEvents.SEGMENT_AI_SAVED.value,
        ]
        assert {item.status for item in outbox_events} == {"processed"}
        assert {item.handler_group for item in outbox_events} == {"segment_handlers"}
        assert all(item.attempts == 1 for item in outbox_events)
        assert all(item.error_message is None for item in outbox_events)
        assert all(item.payload.get("pid") == "segment:outbox-pid" for item in outbox_events)
    finally:
        await close_tortoise()
