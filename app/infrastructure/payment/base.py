from abc import ABC, abstractmethod
from pydantic import BaseModel
from application.account.services import AccountService
from domain.finance.contexts.create_bill_context import CreateBillContext
from core.enums.payment.payment_service import PaymentService
from application.finance.events import PaymentCreatedEvent, BillErrorEvent
from core.di.events import DIPublisher


class BasePaymentProvider[O: BaseModel](ABC):
    """
    Abstract payment provider for handling billing lifecycle and event publication.
    """

    payment_service: PaymentService

    @classmethod
    @abstractmethod
    async def _create_payment(cls,
                              create_bill_context: CreateBillContext,
                              options: O
                              ) -> str | None:
        """
        Create payment and return token
        """
        ...

    @classmethod
    @abstractmethod
    async def _prepare_options(cls, create_bill_context: CreateBillContext, account_service: AccountService) -> O:
        ...

    @classmethod
    async def create_payment(cls,
                             create_bill_context: CreateBillContext,
                             account_service: AccountService
                             ) -> None:
        options = await cls._prepare_options(create_bill_context, account_service)
        try:
            token = await cls._create_payment(create_bill_context, options)
            await DIPublisher[PaymentCreatedEvent].publish(
                payload=PaymentCreatedEvent(
                    account_id=create_bill_context.account_id,
                    credits_amount=create_bill_context.credits_amount,
                    cost=create_bill_context.cost,
                    currency=create_bill_context.currency,
                    payment_service=cls.payment_service,
                    user_ip=create_bill_context.user_ip,
                    token=token
                ),
                group_id=f"account:{create_bill_context.account_id}"
            )
        except Exception as ex:
            DIPublisher[BillErrorEvent].publish_error(
                event_error_model=BillErrorEvent,
                ex=ex,
                step=PaymentCreatedEvent,
                account_id=create_bill_context.account_id,
                payment_service=cls.payment_service.value,
                group_id=f"account:{create_bill_context.account_id}"
            )
            raise
