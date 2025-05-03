from domain.finance.entities import BillEntity
from domain.finance.interfaces import BillRepository
from core.enums.payment.payment_service import PaymentService
from infrastructure.repository.mock.base_repository import BaseMockRepository


class MockBillRepository(BaseMockRepository[BillEntity], BillRepository):
    async def get_by_payment_service_and_transaction(
            self, payment_service: PaymentService, transaction: str
    ) -> BillEntity | None:
        return next(
            (b for b in self.entities.values()
             if b.payment_service == payment_service and b.transaction == transaction),
            None
        )

    async def list_by_account(self, account_id: int) -> list[BillEntity]:
        return [b for b in self.entities.values() if b.account_id == account_id]
