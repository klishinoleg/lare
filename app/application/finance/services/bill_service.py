from domain.finance.entities import BillEntity
from domain.finance.exceptions import BillRetrySuccessError, BillRetryRefundError
from domain.finance.interfaces import BillRepository
from application.finance.dtos.bill import (
    CreateBillDTO,
    UpdateBillDTO,
    BillDTO,
    BillListDTO,
)
from application.abstract.services.crud import BaseCRUDService
from core.enums.repository.types import RepositoryTypes


class BillService(
    BaseCRUDService[
        BillEntity,
        BillRepository,
        BillDTO,
        BillListDTO,
        CreateBillDTO,
        UpdateBillDTO
    ]
):
    """
    CRUD service for managing billing operations and credit transactions.
    """
    entity_class = BillEntity
    entity_repository_type = BillRepository
    repository_type = RepositoryTypes.TORTOISE
    create_dto = CreateBillDTO
    update_dto = UpdateBillDTO
    item_dto = BillDTO
    list_dto = BillListDTO

    async def check_bill_for_payment(self, bill_id: int) -> BillEntity:
        bill = await self.get_by_id(bill_id)
        if not bill:
            raise BillRetrySuccessError("Bill not found")
        if bill.success_time:
            raise BillRetrySuccessError("Bill already paid")
        return bill

    async def check_bill_for_refund(self, bill_id: int) -> BillEntity:
        bill = await self.get_by_id(bill_id)
        if not bill:
            raise BillRetryRefundError("Bill not found")
        if bill.refund_time:
            raise BillRetryRefundError("Bill already refunded")
        return bill
