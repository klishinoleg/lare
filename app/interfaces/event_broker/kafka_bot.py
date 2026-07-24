from application.events.handlers_register.bot import register_bot_brokers
from core.enums.events.broker_types import EventBrokerTypes
from core.registrators.bots_registrator import register_bots
from interfaces.event_broker.initial import before_start as initial_before_start


async def broker_before_start() -> None:
    register_bots()
    await initial_before_start()

broker = register_bot_brokers(EventBrokerTypes.KAFKA)

broker.before_start(broker_before_start)
app = broker.app

if __name__ == "__main__":
    broker.run()
