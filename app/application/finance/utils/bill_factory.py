from application.finance.dtos.bill import CreateBillDTO
from application.finance.events import BillCreatedEvent, BillErrorEvent, BillConfirmedEvent, BillRefundedEvent
from application.finance.services.bill_service import BillService
from core.di.events import DIPublisher
from domain.finance.entities import BillEntity


async def check_bill_for_payment(bill_id: int) -> BillEntity:
    return await BillService().check_bill_for_payment(bill_id)


async def create_bill_event(create_bill_dto: CreateBillDTO, pid: str | None = None) -> int:
    bill_entity = BillEntity(**create_bill_dto.model_dump())
    bill_created = await BillService().create(bill_entity)
    await DIPublisher[BillCreatedEvent, BillErrorEvent].publish(BillCreatedEvent(
        bill_id=bill_created.id,
        account_id=bill_created.account_id,
        credits_amount=bill_created.credits_amount,
        cost=bill_created.cost,
        payment_service=bill_created.payment_service,
        currency=bill_created.currency,
        user_ip=bill_created.user_ip,
        pid=pid
    ), group_id=create_bill_dto.account_id)
    return bill_created.id


async def bill_successful_event(bill_id: int, payment_data: dict, transaction: str | None,
                                token: str | None = None, pid: str | None = None) -> None:
    bill = await BillService().check_bill_for_payment(bill_id)
    await DIPublisher[BillConfirmedEvent, BillErrorEvent].publish(BillConfirmedEvent(
        bill_id=bill_id,
        account_id=bill.account_id,
        transaction=transaction,
        payment_data=payment_data,
        token=token,
        payment_service=bill.payment_service,
        pid=pid
    ))


async def bill_refunded_event(bill_id: int, payment_data: dict, transaction: str | None,
                              token: str | None = None, pid: str | None = None) -> None:
    bill = await BillService().check_bill_for_refund(bill_id)
    await DIPublisher[BillRefundedEvent, BillErrorEvent].publish(BillRefundedEvent(
        bill_id=bill_id,
        account_id=bill.account_id,
        transaction=transaction,
        payment_data=payment_data,
        token=token,
        payment_service=bill.payment_service,
        pid=pid
    ))
