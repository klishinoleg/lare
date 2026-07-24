import typing

from application.text.segment.event_handlers.segment_ai_processing import SegmentAiProcessingHandler
from application.text.segment.event_handlers.segment_ai_received import SegmentAiReceivedHandler
from application.text.segment.event_handlers.segment_ai_requested import SegmentAiRequestedHandler
from application.text.segment.event_handlers.segment_ai_saved import SegmentAiSavedHandler
from application.text.segment.event_handlers.segment_create_requested import SegmentCreateRequestedHandler
from application.text.segment.event_handlers.segment_created import SegmentCreatedHandler
from application.text.segment.event_handlers.segment_error import SegmentErrorHandler
from application.text.segment.events import (
    SegmentAiProcessingEvent,
    SegmentAiReceivedEvent,
    SegmentAiRequestedEvent,
    SegmentAiSavedEvent,
    SegmentCreateRequestedEvent,
    SegmentCreatedEvent,
    SegmentErrorEvent,
)
from core.di.events import DIBrokerManager
from core.enums.events.broker_types import EventBrokerTypes

if typing.TYPE_CHECKING:
    from infrastructure.broker.base_broker import BaseBroker


def register_segment_brokers[BS: "BaseBroker"](
    broker_type: EventBrokerTypes | None = None,
) -> BS:  # type:ignore[type-var, misc]
    broker_manager = DIBrokerManager.get(broker_type)
    broker_manager.subscribe(SegmentCreateRequestedHandler, SegmentCreateRequestedEvent)
    broker_manager.subscribe(SegmentCreatedHandler, SegmentCreatedEvent)
    broker_manager.subscribe(SegmentAiRequestedHandler, SegmentAiRequestedEvent)
    broker_manager.subscribe(SegmentAiProcessingHandler, SegmentAiProcessingEvent)
    broker_manager.subscribe(SegmentAiReceivedHandler, SegmentAiReceivedEvent)
    broker_manager.subscribe(SegmentAiSavedHandler, SegmentAiSavedEvent)
    broker_manager.subscribe(SegmentErrorHandler, SegmentErrorEvent)
    return broker_manager
