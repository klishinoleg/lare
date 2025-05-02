import typing
from application.finance.event_handlers.bill_confirmed import BillConfirmedEvent, BillConfirmedEventHandler
from application.finance.event_handlers.bill_paid import BillPaidEvent, BillPaidEventHandler
from application.finance.event_handlers.bill_payment import BillPaymentEvent, BillPaymentEventHandler
from application.finance.event_handlers.bill_refunded import BillRefundedEvent, BillRefundedEventHandler
from application.finance.event_handlers.bill_created import BillCreatedEvent, BillCreatedEventHandler
from application.finance.event_handlers.bill_error import BillErrorEvent, BillErrorEventHandler
from application.finance.event_handlers.transaction_created import TransactionCreatedEvent, \
    TransactionCreatedEventHandler
from application.finance.event_handlers.transaction_start_bonus import TransactionStartBonusEvent, \
    TransactionStartBonusEventHandler
from application.finance.event_handlers.transaction_error import TransactionErrorEvent, TransactionErrorEventHandler
from application.finance.event_handlers.usage_created import UsageCreatedEvent, UsageCreatedEventHandler
from application.finance.event_handlers.usage_cancelled import UsageCancelledEvent, UsageCancelledEventHandler
from application.finance.event_handlers.usage_error import UsageErrorEvent, UsageErrorEventHandler
from core.di.events import DIBrokerManager
from core.enums.events.broker_types import EventBrokerTypes

if typing.TYPE_CHECKING:
    from infrastructure.broker.base_broker import BaseBroker


def register_finance_main_brokers[BS: "BaseBroker"](broker_type: EventBrokerTypes | None = None,
                                                    bills: bool = True,
                                                    transactions: bool = True,
                                                    usages: bool = True
                                                    ) -> BS:  # type:ignore[type-var, misc]
    broker_manager = DIBrokerManager.get(broker_type)
    if bills:
        broker_manager.subscribe(BillConfirmedEventHandler, BillConfirmedEvent)
        broker_manager.subscribe(BillPaidEventHandler, BillPaidEvent)
        broker_manager.subscribe(BillCreatedEventHandler, BillCreatedEvent)
        broker_manager.subscribe(BillPaymentEventHandler, BillPaymentEvent)
        broker_manager.subscribe(BillRefundedEventHandler, BillRefundedEvent)
        broker_manager.subscribe(BillErrorEventHandler, BillErrorEvent)
    if transactions:
        broker_manager.subscribe(TransactionCreatedEventHandler, TransactionCreatedEvent)
        broker_manager.subscribe(TransactionErrorEventHandler, TransactionErrorEvent)
        broker_manager.subscribe(TransactionStartBonusEventHandler, TransactionStartBonusEvent)
    if usages:
        broker_manager.subscribe(UsageCreatedEventHandler, UsageCreatedEvent)
        broker_manager.subscribe(UsageCancelledEventHandler, UsageCancelledEvent)
        broker_manager.subscribe(UsageErrorEventHandler, UsageErrorEvent)
    return broker_manager
