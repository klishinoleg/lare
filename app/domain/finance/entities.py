from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from domain.abstract import BaseEntity
from domain.finance.enums.account_usage_type import AccountUsageType
from domain.finance.enums.currency import Currency
from core.enums.payment.payment_service import PaymentService
from domain.finance.enums.transaction_type import TransactionType
from domain.mixins.timestamp_mixin import TimestampMixin


@dataclass(slots=True, kw_only=True)
class AccountTransactionEntity(BaseEntity, TimestampMixin):
    account_id: int
    transaction_type: TransactionType
    credits_amount: Decimal
    usage_id: int | None = None
    bill_id: int | None = None


@dataclass(slots=True, kw_only=True)
class AccountUsageEntity(BaseEntity, TimestampMixin):
    account_id: int
    credits_amount: Decimal
    usage_type: AccountUsageType
    usage_amount: int
    canceled_at: datetime | None = None


@dataclass(slots=True, kw_only=True)
class BillEntity(BaseEntity, TimestampMixin):
    account_id: int
    credits_amount: Decimal
    cost: int
    currency: Currency
    payment_service: PaymentService
    payment_data: dict
    success_time: datetime | None = None
    refund_time: datetime | None = None
    transaction: str | None = None
    token: str | None = None
    user_ip: str | None = None
