from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from pydantic import BaseModel
from domain.finance.contexts.create_bill_context import CreateBillContext
from core.enums.payment.payment_service import PaymentService

if TYPE_CHECKING:
    from application.account.services import AccountService


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
    async def _prepare_options(cls, create_bill_context: CreateBillContext, account_service: "AccountService") -> O:
        ...

    @classmethod
    async def create_payment(cls,
                             create_bill_context: CreateBillContext,
                             account_service: "AccountService"
                             ) -> str | None:
        options = await cls._prepare_options(create_bill_context, account_service)
        token = await cls._create_payment(create_bill_context, options)
        return token
