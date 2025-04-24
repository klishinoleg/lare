from domain.finance.entities import BillEntity
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
