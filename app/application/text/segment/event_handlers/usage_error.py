from application.abstract.events import BaseEventHandler
from application.finance.events import UsageErrorEvent
from application.events.handler_groups import HandlerGroups


class UsageErrorEventHandler(BaseEventHandler[UsageErrorEvent, UsageErrorEvent]):
    event_type = UsageErrorEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.SEGMENT

    @classmethod
    async def handler(cls, event: UsageErrorEvent) -> None:
        """
        Handle UsageErrorEventEvent: log the error.
        """
        ...
