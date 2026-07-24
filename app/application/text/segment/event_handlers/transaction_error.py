from application.abstract.events import BaseEventHandler
from application.finance.events import TransactionErrorEvent
from application.events.handler_groups import HandlerGroups


class TransactionErrorEventHandler(BaseEventHandler[TransactionErrorEvent, TransactionErrorEvent]):
    event_type = TransactionErrorEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.SEGMENT

    @classmethod
    @BaseEventHandler.with_streaming
    async def handler(cls, event: TransactionErrorEvent) -> None:
        """
        Handle TransactionErrorEventHandler: log the error.
        """
        ...
