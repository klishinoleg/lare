from application.abstract.events import BaseEventHandler
from application.finance.events import TransactionCreatedEvent
from application.events.handler_groups import HandlerGroups


class TransactionCreatedEventHandler(BaseEventHandler[TransactionCreatedEvent]):
    event_type = TransactionCreatedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    async def handler(cls, event: TransactionCreatedEvent, group_id: int | None) -> None:
        """
        Handle TransactionCreatedEventHandler: log the error.
        """
        ...
