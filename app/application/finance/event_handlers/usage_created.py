from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.finance.events import UsageCreatedEvent, UsageErrorEvent
from application.finance.utils.transaction_factory import create_transaction_from_dto, \
    make_transaction_dto_from_usage_event


class UsageCreatedEventHandler(BaseEventHandler[UsageCreatedEvent, UsageErrorEvent]):
    """
    Handles UsageCreatedEvent: creates a corresponding transaction.
    """
    event_type = UsageCreatedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    @BaseEventHandler.with_error(UsageErrorEvent)
    async def handler(cls, event: UsageCreatedEvent) -> None:
        create_transaction_dto = make_transaction_dto_from_usage_event(event)
        await create_transaction_from_dto(create_transaction_dto, pid=event.pid)
