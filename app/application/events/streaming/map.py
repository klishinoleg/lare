from typing import TYPE_CHECKING
from application.events.streaming.statuses import StreamingStatuses
from application.events.streaming.types import StreamingTypes
from application.events.event_types import FinanceEventTypes, EventTypes, SegmentEvents

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent

STREAMING_MAP = {
    StreamingTypes.START_BONUS.value: {
        FinanceEventTypes.TRANSACTION_START_BONUS.value: StreamingStatuses.PENDING,
        FinanceEventTypes.TRANSACTION_CREATED.value: StreamingStatuses.SUCCEEDED,
        FinanceEventTypes.TRANSACTION_ERROR.value: StreamingStatuses.FAILED
    },
    StreamingTypes.SEGMENT.value: {
        SegmentEvents.SEGMENT_CREATE_REQUESTED.value: StreamingStatuses.PENDING,
        SegmentEvents.SEGMENT_CREATED.value: StreamingStatuses.PENDING,
        SegmentEvents.SEGMENT_AI_REQUESTED.value: StreamingStatuses.AI_REQUEST,
        SegmentEvents.SEGMENT_AI_PROCESSING.value: StreamingStatuses.AI_REQUEST,
        SegmentEvents.SEGMENT_AI_RECEIVED.value: StreamingStatuses.PROCESSING,
        SegmentEvents.SEGMENT_AI_SAVED.value: StreamingStatuses.FINANCE,
        FinanceEventTypes.USAGE_CREATED.value: StreamingStatuses.FINANCE,
        FinanceEventTypes.TRANSACTION_CREATED.value: StreamingStatuses.SUCCEEDED,
        SegmentEvents.SEGMENT_ERROR.value: StreamingStatuses.FAILED
    }
}


def get_streaming_statuses[ET: "EventTypes"](streaming_type: StreamingTypes) -> dict[ET, StreamingStatuses]:
    return STREAMING_MAP[streaming_type.value]


def get_streaming_status[BE: "BaseEvent"](streaming_type: StreamingTypes, event: BE) -> StreamingStatuses | None:
    return STREAMING_MAP.get(streaming_type.value, {}).get(event.event_type.value, None)
