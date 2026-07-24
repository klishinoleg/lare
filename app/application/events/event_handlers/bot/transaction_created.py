from application.abstract.events import BaseEventHandler
from application.account.services import AccountService
from application.finance.events import TransactionCreatedEvent, TransactionErrorEvent
from application.events.handler_groups import HandlerGroups
from core.di.bot import DIBot
from core.messages.bot import GetBotMessages
from domain.finance.enums.transaction_type import TransactionType


class TransactionCreatedEventHandler(BaseEventHandler[TransactionCreatedEvent, TransactionErrorEvent]):
    event_type = TransactionCreatedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.BOT

    @classmethod
    @BaseEventHandler.with_error(TransactionErrorEvent)
    async def handler(cls, event: TransactionCreatedEvent) -> None:
        """
        Handle TransactionCreatedEventHandler: send message in the bot.
        """
        msg = ""
        if event.transaction_type == TransactionType.START_BONUS:
            msg = GetBotMessages.add_credits_start_bonus(event.credits_amount)
        elif event.transaction_type == TransactionType.PAYMENT:
            msg = GetBotMessages.add_credits_bill(event.credits_amount)
        if not msg:
            return
        account_entity = await AccountService().get_by_id(event.account_id)
        bot = await DIBot.get(account_entity=account_entity)
        await bot.send_message(msg)
