from __future__ import annotations

from types import SimpleNamespace

import pytest

from application.text.segment.event_handlers import segment_ai_processing
from application.text.segment.events import SegmentAiProcessingEvent, SegmentAiReceivedEvent
from domain.text_data.enums import TextActionsTypes, TextTranslateTypes


@pytest.mark.asyncio
async def test_segment_ai_processing_uses_registered_reader_provider(monkeypatch) -> None:
    saved_responses: list[dict[str, object]] = []
    published_events: list[tuple[SegmentAiReceivedEvent, str | None]] = []
    provider_requests: list[object] = []

    class FakeSegmentCrudService:
        async def get_by_id(self, segment_id: int) -> SimpleNamespace:
            return SimpleNamespace(id=segment_id, name="hello brave world", language_id=1)

    class FakeSegmentAiLogService:
        async def save_response(
            self,
            *,
            ai_log_id: int,
            content: str,
            action: TextActionsTypes,
        ) -> None:
            saved_responses.append(
                {
                    "ai_log_id": ai_log_id,
                    "content": content,
                    "action": action,
                }
            )

    class FakeReaderAiProvider:
        async def process_segment(self, request: object) -> SimpleNamespace:
            provider_requests.append(request)
            return SimpleNamespace(content="provider translation", provider="fixture")

    async def fake_publish(
        *,
        payload: SegmentAiReceivedEvent,
        group_id: str | None = None,
        broker_type: object | None = None,
    ) -> None:
        published_events.append((payload, group_id))

    monkeypatch.setattr(
        segment_ai_processing,
        "SegmentCrudService",
        lambda: FakeSegmentCrudService(),
    )
    monkeypatch.setattr(
        segment_ai_processing,
        "SegmentAiLogService",
        lambda: FakeSegmentAiLogService(),
    )
    monkeypatch.setattr(
        segment_ai_processing,
        "get_reader_ai_provider",
        lambda: FakeReaderAiProvider(),
        raising=False,
    )
    monkeypatch.setattr(segment_ai_processing.DIPublisher, "publish", fake_publish)

    await segment_ai_processing.SegmentAiProcessingHandler.handler(
        SegmentAiProcessingEvent(
            account_id=10,
            segment_id=20,
            ai_log_id=30,
            query_id="provider-test",
            ai_model="fixture-model",
            action=TextActionsTypes.TRANSLATE,
            translate_type=TextTranslateTypes.TEXT,
            pid="pid-1",
        )
    )

    assert len(provider_requests) == 1
    provider_request = provider_requests[0]
    assert provider_request.account_id == 10
    assert provider_request.segment_id == 20
    assert provider_request.ai_model == "fixture-model"
    assert provider_request.text == "hello brave world"
    assert provider_request.action == TextActionsTypes.TRANSLATE
    assert provider_request.translate_type == TextTranslateTypes.TEXT

    assert saved_responses == [
        {
            "ai_log_id": 30,
            "content": "provider translation",
            "action": TextActionsTypes.TRANSLATE,
        }
    ]
    assert len(published_events) == 1
    published_event, group_id = published_events[0]
    assert published_event.content == "provider translation"
    assert published_event.ai_log_id == 30
    assert published_event.pid == "pid-1"
    assert group_id == "account:10"
