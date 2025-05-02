from application.events.handlers_register.bot import register_bot_brokers
from core.enums.events.broker_types import EventBrokerTypes
from core.registrators.bots_registrator import register_bots
from interfaces.event_broker.initial import before_start
from core.config import settings

broker = register_bot_brokers(EventBrokerTypes.KAFKA)

broker.before_start(before_start)
app = broker.app

if __name__ == "__main__":
    print(f"{settings.tg_bot_token=}")
    register_bots()
    broker.run()
