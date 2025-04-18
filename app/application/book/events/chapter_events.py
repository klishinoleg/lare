from application.abstract.events import BaseEvent


class ChapterCreateRequestedEvent(BaseEvent):
    """
    Event: User requests to create a chapter.
    """
    name: str
    book_id: int
    text: str
    account_id: int | None = None


class ChapterTextProcessedEvent(BaseEvent):
    """
    Event: Text has been processed into words.
    """
    chapter_id: int
    words_json_path: str


class ChapterWordsSavedEvent(BaseEvent):
    """
    Event: Words have been successfully saved into database.
    """
    chapter_id: int
    words_count: int


class ChapterCreationCompletedEvent(BaseEvent):
    """
    Event: Chapter creation successfully completed.
    """
    chapter_id: int
    book_id: int
    account_id: int


class ChapterCreationErrorEvent(BaseEvent):
    """
    Event: Error occurred during chapter creation.
    """
    chapter_id: int | None = None
    book_id: int | None = None
    account_id: int | None = None
    step: str
    error_message: str
    traceback: str | None = None
