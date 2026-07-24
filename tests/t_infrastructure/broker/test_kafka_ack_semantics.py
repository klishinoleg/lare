from __future__ import annotations

import pytest

from application.events.event_types import SegmentEvents
from application.events.handler_groups import HandlerGroups
from application.text.segment.events import SegmentAiSavedEvent
from core.config import settings
from core.db import close_tortoise, init_tortoise
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from infrastructure.broker.kafka import broker as kafka_broker_module
from infrastructure.repository.tortoise.models import EventOutboxModel


class RecordingKafkaBroker:
    last_instance: RecordingKafkaBroker | None = None

    def __init__(self, bootstrap_servers: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.subscribed_handler = None
        self.subscription: dict[str, object] | None = None
        RecordingKafkaBroker.last_instance = self

    def subscriber(self, topic: str, group_id: str, auto_commit: bool):
        self.subscription = {
            "topic": topic,
            "group_id": group_id,
            "auto_commit": auto_commit,
        }

        def decorator(func):
            self.subscribed_handler = func
            return func

        return decorator


class RecordingFastStream:
    def __init__(self, broker: RecordingKafkaBroker) -> None:
        self.broker = broker

    async def run(self) -> None:
        return None

    async def stop(self) -> None:
        return None


class RecordingMessage:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    async def ack(self) -> None:
        self.calls.append("ack")


class SuccessfulHandler:
    event_type = SegmentEvents.SEGMENT_AI_SAVED
    event_handler_group = HandlerGroups.SEGMENT

    @classmethod
    async def execute(cls, event: SegmentAiSavedEvent) -> None:
        event.calls.append("execute")


class FailingHandler:
    event_type = SegmentEvents.SEGMENT_AI_SAVED
    event_handler_group = HandlerGroups.SEGMENT

    @classmethod
    async def execute(cls, event: SegmentAiSavedEvent) -> None:
        event.calls.append("execute")
        raise RuntimeError("handler failed")


class OutboxSuccessfulHandler:
    event_type = SegmentEvents.SEGMENT_AI_SAVED
    event_handler_group = HandlerGroups.SEGMENT
    calls: list[str] = []

    @classmethod
    async def execute(cls, event: SegmentAiSavedEvent) -> None:
        cls.calls.append("execute")


class OutboxFailingHandler:
    event_type = SegmentEvents.SEGMENT_AI_SAVED
    event_handler_group = HandlerGroups.SEGMENT
    calls: list[str] = []

    @classmethod
    async def execute(cls, event: SegmentAiSavedEvent) -> None:
        cls.calls.append("execute")
        raise RuntimeError("outbox handler failed")


class EventProbe:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls


def _subscribe(monkeypatch: pytest.MonkeyPatch, handler_cls):
    monkeypatch.setattr(kafka_broker_module, "KafkaBroker", RecordingKafkaBroker)
    monkeypatch.setattr(kafka_broker_module, "FastStream", RecordingFastStream)
    event_broker = kafka_broker_module.KafkaEventBroker()
    event_broker.subscribe(handler_cls, SegmentAiSavedEvent)
    broker = RecordingKafkaBroker.last_instance
    assert broker is not None
    assert broker.subscription == {
        "topic": SegmentEvents.SEGMENT_AI_SAVED.value,
        "group_id": HandlerGroups.SEGMENT,
        "auto_commit": False,
    }
    assert broker.subscribed_handler is not None
    return broker.subscribed_handler


@pytest.mark.asyncio
async def test_kafka_message_is_acked_after_handler_success(monkeypatch) -> None:
    calls: list[str] = []
    subscribed_handler = _subscribe(monkeypatch, SuccessfulHandler)

    await subscribed_handler(EventProbe(calls), RecordingMessage(calls))

    assert calls == ["execute", "ack"]


@pytest.mark.asyncio
async def test_kafka_message_is_not_acked_when_handler_fails(monkeypatch) -> None:
    calls: list[str] = []
    subscribed_handler = _subscribe(monkeypatch, FailingHandler)

    with pytest.raises(RuntimeError, match="handler failed"):
        await subscribed_handler(EventProbe(calls), RecordingMessage(calls))

    assert calls == ["execute"]


@pytest.mark.asyncio
async def test_kafka_handler_records_processed_outbox_state(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "kafka-outbox-processed.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.KAFKA
    settings.default_event_streaming = EventStreamingTypes.MOCK
    OutboxSuccessfulHandler.calls = []

    await init_tortoise()
    try:
        calls: list[str] = []
        subscribed_handler = _subscribe(monkeypatch, OutboxSuccessfulHandler)
        event = SegmentAiSavedEvent(
            account_id=1,
            segment_id=10,
            ai_log_id=20,
            pid="segment:kafka-outbox-success",
        )

        await subscribed_handler(event, RecordingMessage(calls))

        outbox = await EventOutboxModel.get(
            event_id=str(event.id),
            handler_group=HandlerGroups.SEGMENT,
        )
        assert OutboxSuccessfulHandler.calls == ["execute"]
        assert calls == ["ack"]
        assert outbox.event_type == SegmentEvents.SEGMENT_AI_SAVED.value
        assert outbox.status == "processed"
        assert outbox.attempts == 1
        assert outbox.error_message is None
        assert outbox.pid == "segment:kafka-outbox-success"
        assert outbox.payload["account_id"] == 1
        assert outbox.payload["segment_id"] == 10
        assert outbox.payload["ai_log_id"] == 20
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_kafka_handler_records_failed_outbox_state_without_ack(
    monkeypatch,
    tmp_path,
) -> None:
    db_path = tmp_path / "kafka-outbox-failed.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.KAFKA
    settings.default_event_streaming = EventStreamingTypes.MOCK
    OutboxFailingHandler.calls = []

    await init_tortoise()
    try:
        calls: list[str] = []
        subscribed_handler = _subscribe(monkeypatch, OutboxFailingHandler)
        event = SegmentAiSavedEvent(
            account_id=1,
            segment_id=10,
            ai_log_id=20,
            pid="segment:kafka-outbox-failed",
        )

        with pytest.raises(RuntimeError, match="outbox handler failed"):
            await subscribed_handler(event, RecordingMessage(calls))

        outbox = await EventOutboxModel.get(
            event_id=str(event.id),
            handler_group=HandlerGroups.SEGMENT,
        )
        assert OutboxFailingHandler.calls == ["execute"]
        assert calls == []
        assert outbox.event_type == SegmentEvents.SEGMENT_AI_SAVED.value
        assert outbox.status == "failed"
        assert outbox.attempts == 1
        assert outbox.error_message == "outbox handler failed"
        assert outbox.pid == "segment:kafka-outbox-failed"
    finally:
        await close_tortoise()


@pytest.mark.asyncio
async def test_kafka_handler_dead_letters_and_acks_after_max_failed_attempts(
    monkeypatch,
    tmp_path,
) -> None:
    db_path = tmp_path / "kafka-outbox-dead-letter.sqlite3"
    settings.database_url = f"sqlite://{db_path.as_posix()}"
    settings.slave_database_url = settings.database_url
    settings.event_broker_type = EventBrokerTypes.KAFKA
    settings.default_event_streaming = EventStreamingTypes.MOCK
    OutboxFailingHandler.calls = []

    await init_tortoise()
    try:
        calls: list[str] = []
        subscribed_handler = _subscribe(monkeypatch, OutboxFailingHandler)
        event = SegmentAiSavedEvent(
            account_id=1,
            segment_id=10,
            ai_log_id=20,
            pid="segment:kafka-outbox-dead-letter",
        )

        for _ in range(2):
            with pytest.raises(RuntimeError, match="outbox handler failed"):
                await subscribed_handler(event, RecordingMessage(calls))

        await subscribed_handler(event, RecordingMessage(calls))

        outbox = await EventOutboxModel.get(
            event_id=str(event.id),
            handler_group=HandlerGroups.SEGMENT,
        )
        assert OutboxFailingHandler.calls == ["execute", "execute", "execute"]
        assert calls == ["ack"]
        assert outbox.event_type == SegmentEvents.SEGMENT_AI_SAVED.value
        assert outbox.status == "dead_lettered"
        assert outbox.attempts == 3
        assert outbox.error_message == "outbox handler failed"
        assert outbox.pid == "segment:kafka-outbox-dead-letter"
    finally:
        await close_tortoise()
