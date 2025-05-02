from application.abstract.events import BaseEventHandler
from application.account.services import AccountService
from application.events.event_types import FinanceEventTypes
from application.finance.events import TransactionErrorEvent
from application.events.handler_groups import HandlerGroups
from core.di.bot import DIBot
from core.messages.bot import GetBotMessages


class TransactionErrorEventHandler(BaseEventHandler[TransactionErrorEvent, TransactionErrorEvent]):
    event_type = TransactionErrorEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.BOT

    @classmethod
    async def handler(cls, event: TransactionErrorEvent) -> None:
        """
        Handle TransactionErrorEventHandler: send message.
        """
        msg = event.error_message
        if event.step == FinanceEventTypes.TRANSACTION_START_BONUS:
            msg = GetBotMessages.start_bonus_already_sended()
        account_entity = await AccountService().get_by_id(event.account_id)
        bot = await DIBot.get(account_entity=account_entity)
        await bot.send_message(msg)
