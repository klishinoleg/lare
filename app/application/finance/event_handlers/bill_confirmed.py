from datetime import datetime, timezone
from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.finance.events import BillConfirmedEvent, BillErrorEvent
from application.finance.services.bill_service import BillService
from application.finance.utils.transaction_factory import create_transaction_from_dto, make_transaction_dto_from_bill


class BillConfirmedEventHandler(BaseEventHandler[BillConfirmedEvent, BillErrorEvent]):
    """
    Handles Payment confirmed when paymen confirmed, create transaction for increase the credits balance.
    """
    event_type = BillConfirmedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    @BaseEventHandler.with_error(BillErrorEvent)
    async def handler(cls, event: BillConfirmedEvent) -> None:
        bill_service = BillService()
        bill_entity = await bill_service.check_bill_for_payment(event.bill_id)
        create_transaction_dto = make_transaction_dto_from_bill(bill_entity)
        bill_entity.transaction = event.transaction
        if event.token:
            bill_entity.token = event.token
        bill_entity.success_time = datetime.now(tz=timezone.utc)
        await bill_service.update(entity=bill_entity, is_system=True)
        await create_transaction_from_dto(create_transaction_dto, pid=event.pid)
