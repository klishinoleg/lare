from application.abstract.events import BaseEventHandler
from application.finance.events import TransactionErrorEvent
from application.events.handler_groups import HandlerGroups
from core.di.logger import DILogger


class TransactionErrorEventHandler(BaseEventHandler[TransactionErrorEvent]):
    event_type = TransactionErrorEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    async def handler(cls, event: TransactionErrorEvent, group_id: int | None) -> None:
        """
        Handle TransactionErrorEventHandler: log the error.
        """
        logger = DILogger.get()
        await logger.event_log(event)
