from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.finance.events import BillPaymentEvent, BillErrorEvent
from application.finance.services.bill_service import BillService


class BillPaymentEventHandler(BaseEventHandler[BillPaymentEvent, BillErrorEvent]):
    """
    Handles Payment created event: when the payment is successfully created.
    """
    event_type = BillPaymentEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    @BaseEventHandler.with_error(BillErrorEvent)
    async def handler(cls, event: BillPaymentEvent) -> None:
        if event.token:
            bill_service = BillService()
            bill_entity = await bill_service.get_by_id(event.bill_id)
            bill_entity.token = event.token
            await bill_service.update(entity=bill_entity, is_system=True)
