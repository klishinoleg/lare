from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.finance.events import UsageCancelledEvent, UsageErrorEvent
from application.finance.utils.transaction_factory import create_transaction_from_dto, \
    make_transaction_dto_from_usage_event


class UsageCancelledEventHandler(BaseEventHandler[UsageCancelledEvent, UsageErrorEvent]):
    """
    Handles UsageCancelEvent: Create Cancel usage transaction.
    """
    event_type = UsageCancelledEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    @BaseEventHandler.with_error(UsageErrorEvent)
    async def handler(cls, event: UsageCancelledEvent) -> None:
        create_transaction_dto = make_transaction_dto_from_usage_event(event)
        await create_transaction_from_dto(create_transaction_dto, pid=event.pid)
