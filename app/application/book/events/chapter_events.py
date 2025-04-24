from typing import ClassVar
from application.abstract.events import BaseEvent
from application.events.event_types import EventTypes


class ChapterCreateRequestedEvent(BaseEvent):
    """
    Event: User requests to create a chapter.
    """
    event_type: ClassVar = EventTypes.CHAPTER_CREATE_REQUESTED
    chapter_id: int
    book_id: int
    text: str


class ChapterTextProcessedEvent(BaseEvent):
    """
    Event: Text has been processed into words.
    """
    event_type: ClassVar = EventTypes.CHAPTER_TEXT_PROCESSED
    chapter_id: int
    words_data: list


class ChapterWordsSavedEvent(BaseEvent):
    """
    Event: Words have been successfully saved into database.
    """
    event_type: ClassVar = EventTypes.CHAPTER_WORDS_SAVED
    chapter_id: int
    words_count: int


class ChapterCreationCompletedEvent(BaseEvent):
    """
    Event: Chapter creation successfully completed.
    """
    event_type: ClassVar = EventTypes.CHAPTER_CREATION_COMPLETED
    chapter_id: int
    book_id: int
    account_id: int


class ChapterCreationErrorEvent(BaseEvent):
    """
    Event: Error occurred during chapter creation.
    """
    event_type: ClassVar = EventTypes.CHAPTER_CREATION_ERROR
    chapter_id: int | None = None
    book_id: int | None = None
    account_id: int | None = None
    step: EventTypes
    error_message: str
    traceback: str | None = None
