from typing import ClassVar

from application.abstract.events import BaseEvent, BaseErrorEvent
from application.events.event_types import SegmentEvents
from application.text.segment.dtos import CreateSegmentByWordChapterIndexesDTO
from domain.text_data.enums import TextActionsTypes, TextTranslateTypes


class SegmentCreateRequestedEvent(BaseEvent):
    event_type: ClassVar = SegmentEvents.SEGMENT_CREATE_REQUESTED
    account_id: int
    dto: CreateSegmentByWordChapterIndexesDTO
    ai_model: str


class SegmentCreatedEvent(BaseEvent):
    event_type: ClassVar = SegmentEvents.SEGMENT_CREATED
    account_id: int
    segment_id: int
    ai_model: str = "local-compat"
    action: TextActionsTypes = TextActionsTypes.TRANSLATE
    translate_type: TextTranslateTypes | None = None


class SegmentAiRequestedEvent(BaseEvent):
    event_type: ClassVar = SegmentEvents.SEGMENT_AI_REQUESTED
    account_id: int
    segment_id: int
    ai_log_id: int
    ai_model: str = "local-compat"
    action: TextActionsTypes = TextActionsTypes.TRANSLATE
    translate_type: TextTranslateTypes | None = None


class SegmentAiProcessingEvent(BaseEvent):
    event_type: ClassVar = SegmentEvents.SEGMENT_AI_PROCESSING
    account_id: int
    segment_id: int
    ai_log_id: int
    query_id: str | None
    ai_model: str = "local-compat"
    action: TextActionsTypes = TextActionsTypes.TRANSLATE
    translate_type: TextTranslateTypes | None = None


class SegmentAiReceivedEvent(BaseEvent):
    event_type: ClassVar = SegmentEvents.SEGMENT_AI_RECEIVED
    account_id: int
    segment_id: int
    ai_log_id: int
    content: str
    action: TextActionsTypes = TextActionsTypes.TRANSLATE
    translate_type: TextTranslateTypes | None = None


class SegmentAiSavedEvent(BaseEvent):
    event_type: ClassVar = SegmentEvents.SEGMENT_AI_SAVED
    account_id: int
    segment_id: int
    ai_log_id: int
    action: TextActionsTypes = TextActionsTypes.TRANSLATE
    translate_type: TextTranslateTypes | None = None


class SegmentErrorEvent(BaseErrorEvent):
    event_type: ClassVar = SegmentEvents.SEGMENT_ERROR
    account_id: int
    segment_id: int | None = None
    ai_log_id: int | None = None
