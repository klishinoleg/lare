import typing

from application.events.event_handlers.bot.transaction_error import TransactionErrorEventHandler, TransactionErrorEvent
from application.events.event_handlers.bot.transaction_created import TransactionCreatedEventHandler, \
    TransactionCreatedEvent
from core.di.events import DIBrokerManager
from core.enums.events.broker_types import EventBrokerTypes

if typing.TYPE_CHECKING:
    from infrastructure.broker.base_broker import BaseBroker


def register_bot_brokers[BS: "BaseBroker"](
        broker_type: EventBrokerTypes | None = None) -> BS:  # type:ignore[type-var, misc]
    broker_manager = DIBrokerManager.get(broker_type)
    broker_manager.subscribe(TransactionErrorEventHandler, TransactionErrorEvent)
    broker_manager.subscribe(TransactionCreatedEventHandler, TransactionCreatedEvent)
    return broker_manager
