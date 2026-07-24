from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.text.segment.events import SegmentErrorEvent


class SegmentErrorHandler(BaseEventHandler[SegmentErrorEvent, SegmentErrorEvent]):
    """
    Handles errors that occur during segment creation or AI processing flow.
    This could involve logging, alerting, retries, or marking the segment as failed.
    """
    event_type = SegmentErrorEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.SEGMENT

    @classmethod
    async def handler(cls, event: SegmentErrorEvent) -> None:
        # Example: log or store failure for retries/monitoring
        ...
