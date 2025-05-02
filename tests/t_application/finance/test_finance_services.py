from __future__ import annotations
import uuid
from copy import deepcopy
from decimal import Decimal
import pytest
from application.account.dtos import AccountDTO
from application.account.services import AccountService
from application.auth.dtos import AuthResponseDTO
from application.events.event_types import FinanceEventTypes
from application.events.handlers_register.finance import register_finance_main_brokers
from application.finance.dtos.acount_usage import CreateAccountUsageDTO
from application.finance.dtos.bill import CreateBillDTO
from application.finance.services.bill_service import BillService
from application.finance.utils.bill_factory import create_bill_event, bill_successful_event, bill_refunded_event
from application.finance.utils.manual_bill import parse_manual_bill_message, confirm_manual_bill
from application.finance.utils.transaction_factory import publish_start_bonus_transaction
from application.finance.utils.usage_factory import create_usage_event, cancel_usage_event
from core.enums.payment.payment_service import PaymentService
from domain.account.entities import AccountEntity
from domain.finance.enums.currency import Currency
from domain.finance.enums.transaction_type import TransactionType
from domain.finance.exceptions import BillRetrySuccessError, AccountTransactionStartBonusExist
from tests.t_application.abstract.base_account import BaseAccountTest
from tests.t_application.finance.fake_faktory import CreateBillDTOFactory, CreateAccountUsageDTOFactory
from core.config import settings


class TestFinanceService(BaseAccountTest):

    @pytest.fixture(scope='session', autouse=True)
    def register_events(self) -> None:
        register_finance_main_brokers()

    @pytest.mark.asyncio
    async def test_create_build(self, auth_response: AuthResponseDTO) -> None:
        account = auth_response.account
        mock_create_bill_dto: CreateBillDTO = CreateBillDTOFactory(account_id=account.id,
                                                                   payment_service=PaymentService.MOCK)
        # Create bill
        bill_id = await create_bill_event(mock_create_bill_dto)
        bill = await BillService().get_by_id(bill_id)
        assert bill is not None
        self.check_events(*(
            (FinanceEventTypes.BILL_CREATED, None),
            (FinanceEventTypes.BILL_PAYMENT, {
                "credits_amount": mock_create_bill_dto.credits_amount,
                "cost": mock_create_bill_dto.cost})
        ))
        # Confirm bill
        await bill_successful_event(bill_id=bill_id, payment_data={"test": "ok"}, transaction=str(uuid.uuid4()))
        self.check_events(*(
            (FinanceEventTypes.BILL_CONFIRMED, None),
            (FinanceEventTypes.TRANSACTION_CREATED, {
                "credits_amount": mock_create_bill_dto.credits_amount,
                "transaction_type": TransactionType.PAYMENT,
                "account_id": account.id,
                "bill_id": bill_id
            })
        ))
        bill = await BillService().get_by_id(bill_id)
        assert bill.success_time is not None
        updated_account = deepcopy(await AccountService().get_by_id(account.id))
        assert updated_account.credits == mock_create_bill_dto.credits_amount
        with pytest.raises(BillRetrySuccessError):
            await bill_successful_event(bill_id=bill_id, payment_data={"test": "ok"}, transaction=str(uuid.uuid4()))
        # Refund bill
        await bill_refunded_event(bill_id, transaction=str(uuid.uuid4()), payment_data={"test": "refund"})
        refunded_account = await AccountService().get_by_id(account.id)
        self.check_events(*(
            (FinanceEventTypes.BILL_REFUNDED, {"payment_data": {"test": "refund"}}),
            (FinanceEventTypes.TRANSACTION_CREATED, {"transaction_type": TransactionType.REFUND,
                                                     "credits_amount": -1 * mock_create_bill_dto.credits_amount})
        ))
        assert refunded_account.credits == updated_account.credits - mock_create_bill_dto.credits_amount

    async def create_bill(self, account: AccountDTO) -> tuple[int, AccountEntity]:
        self.get_events()
        mock_create_bill_dto: CreateBillDTO = CreateBillDTOFactory(account_id=account.id,
                                                                   payment_service=PaymentService.MOCK)
        bill_id = await create_bill_event(mock_create_bill_dto)
        await bill_successful_event(bill_id=bill_id, payment_data={"test": "ok"}, transaction=str(uuid.uuid4()))
        assert len(self.get_events()) == 4
        return bill_id, deepcopy(await AccountService().get_by_id(account.id))

    @pytest.mark.asyncio
    async def test_manual_bill(self, auth_response: AuthResponseDTO) -> None:
        account = auth_response.account
        bill_id, account_after_first_bill = await self.create_bill(account)
        credits_amount = Decimal(300)
        cost = 200
        currency = Currency.RUB
        right_message = f"credits:{account.id}:{credits_amount}:{cost}:{currency.value}"
        # Parse input message
        parsed_account, create_bill_dto = await parse_manual_bill_message(right_message)
        assert parsed_account.id == account.id
        assert create_bill_dto.credits_amount == credits_amount
        assert create_bill_dto.currency == currency
        assert create_bill_dto.cost == cost
        assert create_bill_dto.account_id == account.id
        # Create bill
        bill_id = await create_bill_event(create_bill_dto)
        # Confirm manual bill
        await confirm_manual_bill(bill_id=bill_id, transaction=str(uuid.uuid4()),
                                  account=AccountEntity(**account.model_dump()))
        new_account = deepcopy(await AccountService().get_by_id(account.id))
        self.check_events(*(
            (FinanceEventTypes.BILL_CREATED, None),
            (FinanceEventTypes.BILL_PAYMENT, None),
            (FinanceEventTypes.BILL_CONFIRMED, {"payment_data": {"admin": [account.id, account.username]}}),
            (FinanceEventTypes.TRANSACTION_CREATED, {"credits_amount": credits_amount,
                                                     "transaction_type": TransactionType.PAYMENT
                                                     }))
                          )
        assert new_account.credits == credits_amount + account_after_first_bill.credits
        with pytest.raises(BillRetrySuccessError):
            await confirm_manual_bill(bill_id=bill_id, transaction=str(uuid.uuid4()),
                                      account=AccountEntity(**account.model_dump()))

    @pytest.mark.asyncio
    async def test_usage(self, auth_response: AuthResponseDTO) -> None:
        account = deepcopy(auth_response.account)
        bill_id, account_after_first_bill = await self.create_bill(account)
        create_usage_dto: CreateAccountUsageDTO = CreateAccountUsageDTOFactory(account_id=account.id)
        account_usage_entity = await create_usage_event(create_usage_dto)
        self.check_events(*(
            (FinanceEventTypes.USAGE_CREATED, {"usage_type": create_usage_dto.usage_type}),
            (FinanceEventTypes.TRANSACTION_CREATED, {"credits_amount": create_usage_dto.credits_amount * -1,
                                                     "transaction_type": TransactionType.AI_USAGE})
        ))
        account_after_usage = deepcopy(await AccountService().get_by_id(account.id))
        assert account_after_usage.credits == account_after_first_bill.credits - create_usage_dto.credits_amount
        await cancel_usage_event(account_usage_entity)
        account_after_cancel_usage = deepcopy(await AccountService().get_by_id(account.id))
        self.check_events(*(
            (FinanceEventTypes.USAGE_CANCELLED, {"usage_type": create_usage_dto.usage_type,
                                                 "credits_amount": account_usage_entity.credits_amount}),
            (FinanceEventTypes.TRANSACTION_CREATED, {"credits_amount": create_usage_dto.credits_amount,
                                                     "transaction_type": TransactionType.AI_USAGE_CANCEL})
        ))
        assert account_after_cancel_usage.credits == account_after_first_bill.credits

    @pytest.mark.asyncio
    async def test_start_bonus(self, auth_response: AuthResponseDTO) -> None:
        account = deepcopy(auth_response.account)
        await publish_start_bonus_transaction(account_id=account.id)
        self.check_events(*(
            (FinanceEventTypes.TRANSACTION_START_BONUS, None),
            (FinanceEventTypes.TRANSACTION_CREATED, None),
        ))
        account_with_start_bonus = deepcopy(await AccountService().get_by_id(account.id))
        assert account_with_start_bonus.credits == account.credits + settings.credits_start_bonus
        with pytest.raises(AccountTransactionStartBonusExist):
            await publish_start_bonus_transaction(account_id=account.id)
