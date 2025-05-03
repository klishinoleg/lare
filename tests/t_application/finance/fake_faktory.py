import factory
import random
import uuid
from decimal import Decimal

from application.finance.dtos.acount_usage import CreateAccountUsageDTO
from application.finance.dtos.bill import CreateBillDTO
from domain.finance.enums.account_usage_type import AccountUsageType
from domain.finance.enums.currency import Currency
from core.enums.payment.payment_service import PaymentService


class CreateBillDTOFactory(factory.Factory):
    class Meta:
        model = CreateBillDTO

    account_id = factory.Sequence(lambda n: n + 1)
    credits_amount = factory.LazyFunction(lambda: Decimal(random.randint(10, 1000)))
    cost = factory.LazyFunction(lambda: random.randint(100, 10000))
    currency = factory.Iterator(list(Currency))
    payment_service = factory.Iterator(list(PaymentService))
    payment_data = factory.LazyFunction(lambda: {"payment_info": str(uuid.uuid4())})
    user_ip = factory.LazyFunction(lambda: f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}")


class CreateAccountUsageDTOFactory(factory.Factory):
    class Meta:
        model = CreateAccountUsageDTO

    account_id = factory.Sequence(lambda n: n + 1)
    usage_type = factory.Iterator(list(AccountUsageType))
    usage_id = factory.LazyFunction(lambda: random.randint(1000, 9999))
    usage_amount = factory.LazyFunction(lambda: random.randint(1, 100))
    credits_amount = factory.LazyFunction(lambda: Decimal(random.randint(1, 500)))
