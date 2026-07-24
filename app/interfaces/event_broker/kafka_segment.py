from application.events.handlers_register.segment import register_segment_brokers
from core.enums.events.broker_types import EventBrokerTypes
from interfaces.event_broker.initial import before_start

broker = register_segment_brokers(EventBrokerTypes.KAFKA)

broker.before_start(before_start)
app = broker.app

if __name__ == "__main__":
    broker.run()
