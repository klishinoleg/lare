from application.abstract.events import BaseEventHandler
from application.book.events.chapter_events import ChapterCreationCompletedEvent


class ChapterCreationComplitedEventHandler(BaseEventHandler[ChapterCreationCompletedEvent]):
    event_type = ChapterCreationCompletedEvent.event_type

    @classmethod
    async def handler(cls, event: ChapterCreationCompletedEvent, group_id: int | None) -> None:
        """
        No action hangle for close creation actions
        :param event:
        :param group_id:
        :return:
        """
        ...
