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


class PaymentCreatedEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.PAYMENT_CREATED
    account_id: int
    credits_amount: Decimal
    cost: int
    currency: Currency
    payment_service: PaymentService
    user_ip: str | None = None
    token: str | None = None


class BillErrorEvent(BaseErrorEvent):
    event_type: ClassVar = FinanceEventTypes.BILL_ERROR
    account_id: int
    payment_service: PaymentService | None


class PaymentPaidEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.PAYMENT_PAID
    account_id: int
    transaction: str
    payment_data: dict
    token: str | None
    bill_id: int | None


class PaymentConfirmedEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.PAYMENT_CONFIRMED
    account_id: int
    transaction: str
    payment_data: dict
    token: str | None
    bill_id: int | None


class BillSuccessfulEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.BILL_SUCCESSFUL
    bill_id: int
    account_id: int


class PaymentRefundedEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.PAYMENT_REFUNDED
    account_id: int
    transaction: str
    payment_data: dict
    token: str | None
    bill_id: int | None


class BillRefundedEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.BILL_REFUNDED
    bill_id: int
    account_id: int
    transaction: str
    token: str | None


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


class UsageErrorEvent(BaseErrorEvent):
    event_type: ClassVar = FinanceEventTypes.USAGE_ERROR
    usage_id: int
    account_id: int


class TransactionCreatedEvent(BaseEvent):
    event_type: ClassVar = FinanceEventTypes.TRANSACTION_CREATED
    account_id: int
    transaction_type: TransactionType
    credits_amount: Decimal
    usage_id: int | None = None
    bill_id: int | None = None


class TransactionErrorEvent(BaseErrorEvent):
    event_type: ClassVar = FinanceEventTypes.TRANSACTION_ERROR
    account_id: int
