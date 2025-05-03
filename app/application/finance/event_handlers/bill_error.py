from application.abstract.events import BaseEventHandler
from application.finance.events import BillErrorEvent
from application.events.handler_groups import HandlerGroups
from core.di.logger import DILogger


class BillErrorEventHandler(BaseEventHandler[BillErrorEvent, BillErrorEvent]):
    event_type = BillErrorEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    async def handler(cls, event: BillErrorEvent) -> None:
        """
        Handle BillErrorEventHandler: log the error.
        """
        logger = DILogger.get()
        await logger.event_log(event)
