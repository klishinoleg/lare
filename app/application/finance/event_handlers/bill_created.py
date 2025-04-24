from application.abstract.events import BaseEventHandler
from application.account.services import AccountService
from application.events.handler_groups import HandlerGroups
from application.finance.events import BillCreatedEvent
from core.di.payment import DIPayment


class BillCreatedEventHandler(BaseEventHandler[BillCreatedEvent]):
    """
    Handles Bill created event: create and send bill
    """
    event_type = BillCreatedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    async def handler(cls, event: BillCreatedEvent, group_id: int | None) -> None:
        account_service = AccountService()
        await DIPayment.get_provider(event.payment_service).create_payment(event, account_service)
