from __future__ import annotations

import json
from io import StringIO

import pytest

from application.text.segment.events import SegmentAiSavedEvent
from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from domain.text_data.enums import TextActionsTypes, TextTranslateTypes
from infrastructure.broker.event_outbox import OUTBOX_STATUS_DEAD_LETTERED
from infrastructure.repository.tortoise.models import EventOutboxModel


@pytest.mark.asyncio
async def test_outbox_cli_lists_dead_lettered_events_as_json(tmp_path) -> None:
    db_path = tmp_path / "outbox-cli-list.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"

    await init_tortoise()
    try:
        source_event = SegmentAiSavedEvent(
            account_id=1,
            segment_id=2,
            ai_log_id=3,
            action=TextActionsTypes.TRANSLATE,
            translate_type=TextTranslateTypes.TEXT,
            pid="outbox:cli:list",
        )
        await EventOutboxModel.create(
            event_id=str(source_event.id),
            event_type=source_event.event_type.value,
            handler_group="segment_handlers",
            group_id="account:1",
            pid=source_event.pid,
            status=OUTBOX_STATUS_DEAD_LETTERED,
            attempts=3,
            payload=source_event.model_dump(mode="json"),
            error_message="poison event",
        )

        from interfaces.event_broker import outbox_cli

        stdout = StringIO()
        exit_code = await outbox_cli.run(["list", "--status", "dead_lettered"], stdout=stdout)
        payload = json.loads(stdout.getvalue())

        assert exit_code == 0
        assert payload["count"] == 1
        assert payload["items"][0]["event_type"] == source_event.event_type.value
        assert payload["items"][0]["status"] == OUTBOX_STATUS_DEAD_LETTERED
        assert payload["items"][0]["error_message"] == "poison event"
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_outbox_cli_replays_one_event_as_json(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "outbox-cli-replay.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.MOCK
    settings.default_event_streaming = EventStreamingTypes.MOCK
    settings.secret_key = "test-secret"
    settings.images_upload_dir = "local_uploads_test"
    settings.images_upload_url = "uploads"

    async def fake_publish(
        *,
        payload: SegmentAiSavedEvent,
        group_id: str | None = None,
        broker_type: object | None = None,
    ) -> None:
        return None

    from infrastructure.broker import event_outbox_operations

    monkeypatch.setattr(event_outbox_operations.DIPublisher, "publish", fake_publish)

    await init_tortoise()
    try:
        source_event = SegmentAiSavedEvent(
            account_id=1,
            segment_id=2,
            ai_log_id=3,
            action=TextActionsTypes.TRANSLATE,
            translate_type=TextTranslateTypes.TEXT,
            pid="outbox:cli:replay",
        )
        outbox = await EventOutboxModel.create(
            event_id=str(source_event.id),
            event_type=source_event.event_type.value,
            handler_group="segment_handlers",
            group_id="account:1",
            pid=source_event.pid,
            status=OUTBOX_STATUS_DEAD_LETTERED,
            attempts=3,
            payload=source_event.model_dump(mode="json"),
            error_message="poison event",
        )

        from interfaces.event_broker import outbox_cli

        stdout = StringIO()
        exit_code = await outbox_cli.run(["replay", str(outbox.id)], stdout=stdout)
        payload = json.loads(stdout.getvalue())

        assert exit_code == 0
        assert payload["id"] == outbox.id
        assert payload["event_id"] == str(source_event.id)
        assert payload["status"] == "replay_requested"
    finally:
        await close_tortoise()
