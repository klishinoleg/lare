from abc import abstractmethod
from domain.abstract.interfaces.repository import EntityRepository
from domain.finance.entities import (
    AccountTransactionEntity,
    AccountUsageEntity,
    BillEntity
)
from core.enums.payment.payment_service import PaymentService
from domain.finance.enums.transaction_type import TransactionType


class AccountTransactionRepository(EntityRepository[AccountTransactionEntity]):
    @abstractmethod
    async def list_by_account(self, account_id: int) -> list[AccountTransactionEntity]:
        ...

    @abstractmethod
    async def list_by_account_and_transaction_type(
            self, account_id: int, transaction_type: TransactionType) -> list[AccountTransactionEntity]:
        ...

    @abstractmethod
    async def check_usage_exist(self, usage_id: int) -> bool:
        ...

    @abstractmethod
    async def check_bill_and_transaction_type_exist(self, bill_id: int, transaction_type: TransactionType) -> bool:
        ...


class AccountUsageRepository(EntityRepository[AccountUsageEntity]):
    @abstractmethod
    async def list_by_account(self, account_id: int) -> list[AccountUsageEntity]:
        ...


class BillRepository(EntityRepository[BillEntity]):
    @abstractmethod
    async def get_by_payment_service_and_transaction(
            self, payment_service: PaymentService, transaction: str) -> BillEntity | None:
        ...

    @abstractmethod
    async def list_by_account(self, account_id: int) -> list[BillEntity]:
        ...
