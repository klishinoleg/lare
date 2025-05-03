from application.abstract.events import BaseEventHandler
from application.book.events.chapter_events import ChapterCreationCompletedEvent, ChapterCreationErrorEvent
from application.events.handler_groups import HandlerGroups


class ChapterCreationComplitedEventHandler(BaseEventHandler[ChapterCreationCompletedEvent, ChapterCreationErrorEvent]):
    event_type = ChapterCreationCompletedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.CHAPTER

    @classmethod
    async def handler(cls, event: ChapterCreationCompletedEvent) -> None:
        """
        No action hangle for close creation actions
        :param event:
        :param group_id:
        :return:
        """
        ...
