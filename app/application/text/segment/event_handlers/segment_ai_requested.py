from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.text.segment.events import SegmentAiProcessingEvent, SegmentAiRequestedEvent, SegmentErrorEvent
from core.di.events import DIPublisher


class SegmentAiRequestedHandler(BaseEventHandler[SegmentAiRequestedEvent, SegmentErrorEvent]):
    """
    Triggers the actual AI call (e.g., translation or voice generation) for a segment.
    """
    event_type = SegmentAiRequestedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.SEGMENT

    @classmethod
    @BaseEventHandler.with_error(SegmentErrorEvent)
    async def handler(cls, event: SegmentAiRequestedEvent) -> None:
        await DIPublisher[SegmentAiProcessingEvent, SegmentErrorEvent].publish(
            payload=SegmentAiProcessingEvent(
                account_id=event.account_id,
                segment_id=event.segment_id,
                ai_log_id=event.ai_log_id,
                query_id=f"local-segment-{event.segment_id}",
                ai_model=event.ai_model,
                action=event.action,
                translate_type=event.translate_type,
                pid=event.pid,
            ),
            group_id=f"account:{event.account_id}",
        )
