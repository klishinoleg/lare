from decimal import Decimal
from pydantic import BaseModel
from core.enums.payment.payment_service import PaymentService
from domain.finance.enums.currency import Currency


class CreateBillContext(BaseModel):
    bill_id: int
    account_id: int
    credits_amount: Decimal
    cost: int
    currency: Currency
    payment_service: PaymentService
    user_ip: str | None = None
