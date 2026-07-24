from application.abstract.events import BaseEventHandler
from application.finance.events import TransactionCreatedEvent, TransactionErrorEvent
from application.events.handler_groups import HandlerGroups


class TransactionCreatedEventHandler(BaseEventHandler[TransactionCreatedEvent, TransactionErrorEvent]):
    event_type = TransactionCreatedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.SEGMENT

    @classmethod
    @BaseEventHandler.with_streaming
    async def handler(cls, event: TransactionCreatedEvent) -> None:
        """
        Handle TransactionCreatedEventHandler: log the error.
        """
        ...
