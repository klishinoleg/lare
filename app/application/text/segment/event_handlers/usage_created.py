from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.finance.events import UsageCreatedEvent, UsageErrorEvent
from application.finance.utils.transaction_factory import create_transaction_from_dto, \
    make_transaction_dto_from_usage_event


class UsageCreatedEventHandler(BaseEventHandler[UsageCreatedEvent, UsageErrorEvent]):
    """
    Handles UsageCreatedEvent: change status
    """
    event_type = UsageCreatedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.SEGMENT

    @classmethod
    @BaseEventHandler.with_streaming
    @BaseEventHandler.with_error(UsageErrorEvent)
    async def handler(cls, event: UsageCreatedEvent) -> None:
        ...
