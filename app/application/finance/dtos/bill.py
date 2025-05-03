from decimal import Decimal
from datetime import datetime
from pydantic import Field
from domain.finance.enums.currency import Currency
from core.enums.payment.payment_service import PaymentService
from application.abstract.dtos import BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemDTO, BaseItemsListDTO


class CreateBillDTO(BaseCreateItemDTO):
    """
    DTO used to create a new bill for credit purchase or payment tracking.
    """
    account_id: int = Field(..., description="The ID of the account receiving the bill.")
    credits_amount: Decimal = Field(..., description="The amount of credits associated with this bill.")
    cost: int = Field(..., description="The external currency cost for the bill.")
    currency: Currency = Field(..., description="The billing currency.")
    payment_service: PaymentService = Field(..., description="The service used to issue the bill.")
    payment_data: dict = Field(default_factory=dict, description="Raw data from the payment service.")
    user_ip: str | None = Field(None, description="IP address of the user at time of bill creation.")


class UpdateBillDTO(BaseUpdateItemDTO):
    """
    DTO used to update a bill, e.g. after payment confirmation or refund.
    """
    success_time: datetime | None = Field(None, description="Timestamp when the payment was successfully processed.")
    refund_time: datetime | None = Field(None, description="Timestamp when the payment was refunded.")
    transaction: str | None = Field(None, description="External transaction ID from the payment service.")
    token: str | None = Field(None, description="Unique token for tracking or resolving the payment.")
    payment_data: dict | None = Field(None, description="Updated or appended data from the payment service.")


class BillDTO(BaseItemDTO):
    """
    DTO representing a complete view of a bill.
    """
    id: int = Field(..., description="Unique identifier of the bill.")
    account_id: int = Field(..., description="The ID of the account receiving the bill.")
    credits_amount: Decimal = Field(..., description="The amount of credits associated with this bill.")
    cost: int = Field(..., description="The cost of the bill in real currency.")
    currency: Currency = Field(..., description="The currency in which the bill was issued.")
    payment_service: PaymentService = Field(..., description="The payment service used.")
    payment_data: dict = Field(..., description="Data returned from the payment system.")
    success_time: datetime | None = Field(None, description="Timestamp of successful payment.")
    refund_time: datetime | None = Field(None, description="Timestamp of refund, if applicable.")
    transaction: str | None = Field(None, description="Transaction reference ID.")
    token: str | None = Field(None, description="Internal token for processing the bill.")
    user_ip: str | None = Field(None, description="User IP address at time of payment.")


class BillListDTO(BaseItemsListDTO):
    """
    DTO representing a summary of a bill for list views.
    """
    id: int = Field(..., description="Unique identifier of the bill.")
    credits_amount: Decimal = Field(..., description="The amount of credits provided by the bill.")
    cost: int = Field(..., description="The monetary cost of the bill.")
    currency: Currency = Field(..., description="The currency used in the bill.")
    payment_service: PaymentService = Field(..., description="The name of the service that processed the payment.")
