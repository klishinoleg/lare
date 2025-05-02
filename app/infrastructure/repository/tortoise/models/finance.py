from tortoise import fields
from typing import TYPE_CHECKING

from core.enums.payment.payment_service import PaymentService
from domain.finance.enums.account_usage_type import AccountUsageType
from domain.finance.enums.currency import Currency
from domain.finance.enums.transaction_type import TransactionType
from .abstract import AbstractModel
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .account import AccountModel


class AccountUsageModel(AbstractModel, TimestampMixin):
    id = fields.IntField(primary_key=True)
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel", related_name="usages", on_delete=fields.CASCADE
    )
    credits_amount = fields.DecimalField(max_digits=10, decimal_places=2)
    usage_id = fields.IntField(null=True)
    usage_type = fields.CharEnumField(enum_type=AccountUsageType, max_length=32)
    usage_amount = fields.IntField()
    canceled_at = fields.DatetimeField(null=True)

    if TYPE_CHECKING:
        account_id: int

    class Meta:
        table = "finance_usages"


class BillModel(AbstractModel, TimestampMixin):
    id = fields.IntField(primary_key=True)
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel", related_name="bills", on_delete=fields.CASCADE
    )
    credits_amount = fields.DecimalField(max_digits=10, decimal_places=2)
    cost = fields.IntField()
    currency = fields.CharEnumField(enum_type=Currency, max_length=8)
    payment_service = fields.CharEnumField(enum_type=PaymentService, max_length=32)
    payment_data: dict = fields.JSONField(default=dict)
    success_time = fields.DatetimeField(null=True)
    refund_time = fields.DatetimeField(null=True)
    transaction = fields.CharField(max_length=255, null=True)
    token = fields.CharField(max_length=255, null=True)
    user_ip = fields.CharField(max_length=45, null=True)

    if TYPE_CHECKING:
        account_id: int

    class Meta:
        table = "finance_bills"


class AccountTransactionModel(AbstractModel, TimestampMixin):
    id = fields.IntField(primary_key=True)
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel", related_name="transactions", on_delete=fields.CASCADE
    )
    transaction_type = fields.CharEnumField(enum_type=TransactionType, max_length=32)
    credits_amount = fields.DecimalField(max_digits=10, decimal_places=2)
    usage: fields.ForeignKeyRelation["AccountUsageModel"] | None = fields.ForeignKeyField(
        "models.AccountUsageModel", related_name="transactions", on_delete=fields.CASCADE, null=True
    )
    bill: fields.ForeignKeyRelation["BillModel"] | None = fields.ForeignKeyField(
        "models.BillModel", related_name="transactions", on_delete=fields.CASCADE, null=True
    )

    if TYPE_CHECKING:
        account_id: int
        bill_id: int | None
        usage_id: int | None

    class Meta:
        table = "finance_transactions"
