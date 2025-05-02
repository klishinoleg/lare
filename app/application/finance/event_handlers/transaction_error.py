from application.abstract.events import BaseEventHandler
from application.finance.events import TransactionErrorEvent
from application.events.handler_groups import HandlerGroups
from core.di.logger import DILogger


class TransactionErrorEventHandler(BaseEventHandler[TransactionErrorEvent, TransactionErrorEvent]):
    event_type = TransactionErrorEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    @BaseEventHandler.with_streaming
    async def handler(cls, event: TransactionErrorEvent) -> None:
        """
        Handle TransactionErrorEventHandler: log the error.
        """
        logger = DILogger.get()
        await logger.event_log(event)
