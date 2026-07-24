from __future__ import annotations

from uuid import UUID

import pytest

from application.text.segment.events import SegmentAiSavedEvent
from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from domain.text_data.enums import TextActionsTypes, TextTranslateTypes
from infrastructure.broker.event_outbox import (
    OUTBOX_STATUS_DEAD_LETTERED,
    OUTBOX_STATUS_FAILED,
)
from infrastructure.repository.tortoise.models import EventOutboxModel


@pytest.mark.asyncio
async def test_event_outbox_operations_list_failed_and_dead_lettered_events(tmp_path) -> None:
    db_path = tmp_path / "outbox-operations-list.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"

    await init_tortoise()
    try:
        first_event = SegmentAiSavedEvent(
            account_id=1,
            segment_id=10,
            ai_log_id=20,
            action=TextActionsTypes.TRANSLATE,
            translate_type=TextTranslateTypes.TEXT,
            pid="outbox:list:1",
        )
        second_event = SegmentAiSavedEvent(
            account_id=2,
            segment_id=11,
            ai_log_id=21,
            action=TextActionsTypes.TRANSLATE,
            translate_type=TextTranslateTypes.TEXT,
            pid="outbox:list:2",
        )
        await EventOutboxModel.create(
            event_id=str(first_event.id),
            event_type=first_event.event_type.value,
            handler_group="segment_handlers",
            group_id="account:1",
            pid=first_event.pid,
            status=OUTBOX_STATUS_FAILED,
            attempts=2,
            payload=first_event.model_dump(mode="json"),
            error_message="temporary failure",
        )
        await EventOutboxModel.create(
            event_id=str(second_event.id),
            event_type=second_event.event_type.value,
            handler_group="segment_handlers",
            group_id="account:2",
            pid=second_event.pid,
            status=OUTBOX_STATUS_DEAD_LETTERED,
            attempts=3,
            payload=second_event.model_dump(mode="json"),
            error_message="poison event",
        )

        from infrastructure.broker.event_outbox_operations import EventOutboxOperations

        events = await EventOutboxOperations().list_failed(limit=10)

        assert [event.status for event in events] == [
            OUTBOX_STATUS_DEAD_LETTERED,
            OUTBOX_STATUS_FAILED,
        ]
        assert events[0].event_id == str(second_event.id)
        assert events[0].event_type == second_event.event_type.value
        assert events[0].handler_group == "segment_handlers"
        assert events[0].group_id == "account:2"
        assert events[0].attempts == 3
        assert events[0].error_message == "poison event"
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_event_outbox_operations_replay_republishes_saved_payload(
    monkeypatch,
    tmp_path,
) -> None:
    db_path = tmp_path / "outbox-operations-replay.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"

    published: list[tuple[SegmentAiSavedEvent, str | None]] = []

    async def fake_publish(
        *,
        payload: SegmentAiSavedEvent,
        group_id: str | None = None,
        broker_type: object | None = None,
    ) -> None:
        published.append((payload, group_id))

    from infrastructure.broker import event_outbox_operations

    monkeypatch.setattr(event_outbox_operations.DIPublisher, "publish", fake_publish)

    await init_tortoise()
    try:
        source_event = SegmentAiSavedEvent(
            account_id=10,
            segment_id=20,
            ai_log_id=30,
            action=TextActionsTypes.TRANSLATE,
            translate_type=TextTranslateTypes.TEXT,
            pid="outbox:replay",
        )
        outbox = await EventOutboxModel.create(
            event_id=str(source_event.id),
            event_type=source_event.event_type.value,
            handler_group="segment_handlers",
            group_id="account:10",
            pid=source_event.pid,
            status=OUTBOX_STATUS_DEAD_LETTERED,
            attempts=3,
            payload=source_event.model_dump(mode="json"),
            error_message="poison event",
        )

        result = await event_outbox_operations.EventOutboxOperations().replay(outbox.id)
        updated = await EventOutboxModel.get(id=outbox.id)

        assert result.event_id == str(source_event.id)
        assert result.status == "replay_requested"
        assert updated.status == "replay_requested"
        assert updated.error_message is None
        assert len(published) == 1
        payload, group_id = published[0]
        assert isinstance(payload, SegmentAiSavedEvent)
        assert payload.id == UUID(str(source_event.id))
        assert payload.account_id == 10
        assert payload.segment_id == 20
        assert payload.ai_log_id == 30
        assert group_id == "account:10"
    finally:
        await close_tortoise()
