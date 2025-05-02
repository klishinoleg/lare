from typing import TYPE_CHECKING
from application.events.streaming.statuses import StreamingStatuses
from application.events.streaming.types import StreamingTypes
from application.events.event_types import FinanceEventTypes, EventTypes

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent

STREAMING_MAP = {
    StreamingTypes.START_BONUS.value: {
        FinanceEventTypes.TRANSACTION_START_BONUS.value: StreamingStatuses.PENDING,
        FinanceEventTypes.TRANSACTION_CREATED.value: StreamingStatuses.SUCCEEDED,
        FinanceEventTypes.TRANSACTION_ERROR.value: StreamingStatuses.FAILED
    }
}


def get_streaming_statuses[ET: "EventTypes"](streaming_type: StreamingTypes) -> dict[ET, StreamingStatuses]:
    return STREAMING_MAP[streaming_type.value]


def get_streaming_status[BE: "BaseEvent"](streaming_type: StreamingTypes, event: BE) -> StreamingStatuses | None:
    return STREAMING_MAP.get(streaming_type.value, {}).get(event.event_type.value, None)
