from domain.finance.entities import BillEntity
from domain.finance.interfaces import BillRepository
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from infrastructure.repository.tortoise.models.finance import BillModel
from core.enums.payment.payment_service import PaymentService


class TortoiseBillRepository(BaseTortoiseRepository[BillEntity, BillModel], BillRepository):
    model = BillModel

    async def to_entity(self, o: BillModel) -> BillEntity:
        return BillEntity(
            id=o.id,
            account_id=o.account_id,
            credits_amount=o.credits_amount,
            cost=o.cost,
            currency=o.currency,
            payment_service=o.payment_service,
            payment_data=o.payment_data,
            success_time=o.success_time,
            refund_time=o.refund_time,
            transaction=o.transaction,
            token=o.token,
            user_ip=o.user_ip,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )

    @BaseTortoiseRepository.read()
    async def get_by_payment_service_and_transaction(self, payment_service: PaymentService,
                                                     transaction: str) -> BillEntity | None:
        model = await BillModel.get_or_none(payment_service=payment_service, transaction=transaction)
        return await self.to_entity(model) if model else None

    @BaseTortoiseRepository.read()
    async def list_by_account(self, account_id: int) -> list[BillEntity]:
        models = await BillModel.filter(account_id=account_id).all()
        return [await self.to_entity(model) for model in models]
