from application.abstract.events import BaseEventHandler
from application.book.events.chapter_events import ChapterCreationErrorEvent
from application.events.handler_groups import HandlerGroups
from core.di.logger import DILogger


class ChapterCreationErrorEventHandler(BaseEventHandler[ChapterCreationErrorEvent, ChapterCreationErrorEvent]):
    event_type = ChapterCreationErrorEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.CHAPTER

    @classmethod
    async def handler(cls, event: ChapterCreationErrorEvent) -> None:
        """
        Handle ChapterCreationErrorEvent: log the error.
        """
        logger = DILogger.get()
        await logger.event_log(event)
