from application.abstract.events import BaseEventHandler
from application.account.services import AccountService
from application.events.handler_groups import HandlerGroups
from application.finance.events import BillCreatedEvent, BillPaymentEvent, BillErrorEvent
from core.di.events import DIPublisher
from core.di.payment import DIPayment


class BillCreatedEventHandler(BaseEventHandler[BillCreatedEvent, BillErrorEvent]):
    """
    Handles Bill created event: create and send bill
    """
    event_type = BillCreatedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.FINANCE

    @classmethod
    @BaseEventHandler.with_error(BillErrorEvent)
    async def handler(cls, event: BillCreatedEvent) -> None:
        account_service = AccountService()
        token = await DIPayment.get_provider(event.payment_service).create_payment(event, account_service)
        await DIPublisher[BillPaymentEvent, BillErrorEvent].publish(
            payload=BillPaymentEvent(
                pid=event.pid,
                bill_id=event.bill_id,
                account_id=event.account_id,
                credits_amount=event.credits_amount,
                cost=event.cost,
                currency=event.currency,
                payment_service=event.payment_service,
                token=token
            ),
            group_id=f"account:{event.account_id}"
        )
