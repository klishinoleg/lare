from application.abstract.events import BaseEventHandler
from application.book.events.chapter_events import ChapterCreationCompletedEvent
from application.events.handler_groups import HandlerGroups


class ChapterCreationComplitedEventHandler(BaseEventHandler[ChapterCreationCompletedEvent]):
    event_type = ChapterCreationCompletedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.CHAPTER

    @classmethod
    async def handler(cls, event: ChapterCreationCompletedEvent, group_id: int | None) -> None:
        """
        No action hangle for close creation actions
        :param event:
        :param group_id:
        :return:
        """
        ...
