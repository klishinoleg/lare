from datetime import datetime, timezone
from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.finance.events import BillRefundedEvent, BillErrorEvent
from application.finance.services.bill_service import BillService
from application.finance.utils.transaction_factory import create_transaction_from_dto, make_transaction_dto_from_bill
from domain.finance.exceptions import BillRetryRefundError


class BillRefundedEventHandler(BaseEventHandler[BillRefundedEvent, BillErrorEvent]):
    """
    Handles Payment refunded, create transaction for decrease the credits balance.
    """
    event_type = BillRefundedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    @BaseEventHandler.with_error(BillErrorEvent)
    async def handler(cls, event: BillRefundedEvent) -> None:
        bill_service = BillService()
        bill_entity = await bill_service.get_by_id(event.bill_id)
        if bill_entity.refund_time:
            raise BillRetryRefundError
        create_transaction_dto = make_transaction_dto_from_bill(bill_entity, True)
        bill_entity.payment_data["success_transaction"] = str(bill_entity.transaction)
        bill_entity.transaction = event.transaction
        bill_entity.payment_data["refund"] = event.payment_data
        bill_entity.payment_data["success_transaction"] = event.payment_data
        if event.token:
            bill_entity.token = event.token
        bill_entity.success_time = datetime.now(tz=timezone.utc)
        await bill_service.update(entity=bill_entity, is_system=True)
        await create_transaction_from_dto(create_transaction_dto, pid=event.pid)
