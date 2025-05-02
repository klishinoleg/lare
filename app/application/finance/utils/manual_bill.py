import re
from decimal import Decimal
from application.account.services import AccountService
from application.finance.dtos.bill import CreateBillDTO
from application.finance.services.bill_service import BillService
from application.finance.utils.bill_factory import bill_successful_event
from core.enums.payment.payment_service import PaymentService
from core.messages.exceptions import GetExMessages
from core.messages.finance import GetFinanceMessages
from domain.account.entities import AccountEntity
from domain.finance.enums.currency import Currency

PATTERN_CREDITS_MESSAGE = r"^credits:(\d+):(\d+):(\d+)(?::([A-Za-z]{3,4}))?$"


async def parse_manual_bill_message(message: str) -> tuple[AccountEntity, CreateBillDTO]:
    """
    Parse a manual payment creation request message and return account + CreateBillDTO.
    Raises ValidationError if invalid.
    """
    match = re.match(PATTERN_CREDITS_MESSAGE, message)
    if not match:
        raise ValueError(GetFinanceMessages.manual_bill_message_format())
    account_id, credits_amount, cost, currency = match.groups()
    account = await AccountService().get_by_id(int(account_id))
    if not account:
        raise ValueError(GetExMessages.account_not_found(account_id))

    if not credits_amount.isdigit() or not cost.isdigit():
        raise ValueError(GetFinanceMessages.incorrect_credits_or_cost_format())

    try:
        currency_enum = Currency(currency.upper()) if currency else Currency.RUB
    except ValueError:
        currency_enum = Currency.RUB

    dto = CreateBillDTO(
        account_id=account.id,
        credits_amount=Decimal(credits_amount),
        cost=int(cost),
        payment_service=PaymentService.MANUAL,
        currency=currency_enum
    )
    return account, dto


async def confirm_manual_bill(bill_id: int, transaction: str, account: AccountEntity) -> None:
    await bill_successful_event(bill_id=bill_id, transaction=transaction, token=None,
                                payment_data={"admin": [account.id, account.username]})


async def delete_manual_bill(bill_id: int) -> None:
    bill_sevice = BillService()
    bill = await bill_sevice.get_by_id(bill_id)
    if bill:
        await bill_sevice.delete(bill, is_system=True)
