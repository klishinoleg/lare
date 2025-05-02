from typing import ClassVar
from decimal import Decimal
from application.abstract.events import BaseEvent, BaseErrorEvent
from application.events.event_types import FinanceEventTypes
from domain.finance.contexts.create_bill_context import CreateBillContext
from domain.finance.enums.account_usage_type import AccountUsageType
from domain.finance.enums.currency import Currency
from core.enums.payment.payment_service import PaymentService
from domain.finance.enums.transaction_type import TransactionType


class BillCreatedEvent(BaseEvent, CreateBillContext):
    event_type: ClassVar = FinanceEventTypes.BILL_CREATED
    bill_id: int
    account_id: int
    credits_amount: Decimal
    cost: int
    payment_service: PaymentService


class BillPaymentEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.BILL_PAYMENT
    bill_id: int
    account_id: int
    credits_amount: Decimal
    cost: int
    currency: Currency
    payment_service: PaymentService
    token: str | None = None


class BillErrorEvent(BaseErrorEvent[FinanceEventTypes]):
    event_type: ClassVar = FinanceEventTypes.BILL_ERROR
    account_id: int
    payment_service: PaymentService | None


class BillPaidEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.BILL_PAID
    account_id: int
    transaction: str
    payment_data: dict
    token: str | None
    bill_id: int | None
    payment_service: PaymentService


class BillConfirmedEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.BILL_CONFIRMED
    account_id: int
    transaction: str
    payment_data: dict
    bill_id: int
    token: str | None
    payment_service: PaymentService


class BillRefundedEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.BILL_REFUNDED
    account_id: int
    transaction: str
    payment_data: dict
    token: str | None
    bill_id: int | None
    payment_service: PaymentService


class UsageCreatedEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.USAGE_CREATED
    usage_type: AccountUsageType
    credits_amount: Decimal
    usage_id: int
    account_id: int


class UsageCancelledEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.USAGE_CANCELLED
    usage_type: AccountUsageType
    credits_amount: Decimal
    usage_id: int
    account_id: int


class UsageErrorEvent(BaseErrorEvent[FinanceEventTypes]):
    event_type: ClassVar = FinanceEventTypes.USAGE_ERROR
    usage_id: int | None
    account_id: int
    usage_type: AccountUsageType | None
    credits_amount: Decimal | None


class TransactionCreatedEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.TRANSACTION_CREATED
    account_id: int
    transaction_type: TransactionType
    credits_amount: Decimal
    usage_id: int | None = None
    bill_id: int | None = None


class TransactionStartBonusEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.TRANSACTION_START_BONUS
    account_id: int


class TransactionErrorEvent(BaseErrorEvent[FinanceEventTypes]):
    event_type: ClassVar = FinanceEventTypes.TRANSACTION_ERROR
    account_id: int
