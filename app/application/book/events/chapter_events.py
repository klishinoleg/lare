from typing import ClassVar
from application.abstract.events import BaseEvent, BaseErrorEvent
from application.events.event_types import ChapterEventTypes


class ChapterCreateRequestedEvent(BaseEvent):
    """
    Event: User requests to create a chapter.
    """
    event_type: ClassVar = ChapterEventTypes.CREATE_REQUESTED
    chapter_id: int
    book_id: int
    text: str


class ChapterTextProcessedEvent(BaseEvent):
    """
    Event: Text has been processed into words.
    """
    event_type: ClassVar = ChapterEventTypes.TEXT_PROCESSED
    chapter_id: int
    words_data: list


class ChapterWordsSavedEvent(BaseEvent):
    """
    Event: Words have been successfully saved into database.
    """
    event_type: ClassVar = ChapterEventTypes.WORDS_SAVED
    chapter_id: int
    words_count: int


class ChapterCreationCompletedEvent(BaseEvent):
    """
    Event: Chapter creation successfully completed.
    """
    event_type: ClassVar = ChapterEventTypes.CREATION_COMPLETED
    chapter_id: int
    book_id: int
    account_id: int


class ChapterCreationErrorEvent(BaseErrorEvent[ChapterEventTypes]):
    """
    Event: Error occurred during chapter creation.
    """
    event_type: ClassVar = ChapterEventTypes.CREATION_ERROR
    chapter_id: int | None = None
    book_id: int | None = None
    account_id: int | None = None
