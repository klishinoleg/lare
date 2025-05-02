from application.events.handlers_register.finance import register_finance_main_brokers
from core.enums.events.broker_types import EventBrokerTypes
from interfaces.event_broker.initial import before_start

broker = register_finance_main_brokers(EventBrokerTypes.KAFKA)

broker.before_start(before_start)
app = broker.app

if __name__ == "__main__":
    broker.run()
