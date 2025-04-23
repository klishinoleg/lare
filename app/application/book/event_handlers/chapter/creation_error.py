from application.abstract.events import BaseEventHandler
from application.book.events.chapter_events import ChapterCreationErrorEvent
from core.di.logger import DILogger


class ChapterCreationErrorEventHandler(BaseEventHandler[ChapterCreationErrorEvent]):
    event_type = ChapterCreationErrorEvent.event_type

    @classmethod
    async def handler(cls, event: ChapterCreationErrorEvent, group_id: int | None) -> None:
        """
        Handle ChapterCreationErrorEvent: log the error.
        """
        logger = DILogger.get()
        await logger.event_log(event)
