import uuid
from typing import TYPE_CHECKING
from pydantic import BaseModel
from domain.finance.contexts.create_bill_context import CreateBillContext
from infrastructure.payment.base import BasePaymentProvider

if TYPE_CHECKING:
    from application.account.services import AccountService


class ManualOptions(BaseModel):
    account_id: int


class ManualPaymentProvider(BasePaymentProvider[ManualOptions]):

    @classmethod
    async def _create_payment(cls,
                              create_bill_context: CreateBillContext,
                              options: ManualOptions
                              ) -> str | None:
        return str(uuid.uuid4())

    @classmethod
    async def _prepare_options(cls, create_bill_context: CreateBillContext,
                               account_service: "AccountService") -> ManualOptions:
        return ManualOptions(account_id=create_bill_context.account_id)
