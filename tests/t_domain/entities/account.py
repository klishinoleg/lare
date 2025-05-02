import factory
from domain.account.entities import AccountEntity


class AccountFactory(factory.Factory):
    class Meta:
        model = AccountEntity

    id = None
    username = factory.Faker("user_name")
    email = factory.Faker("email")
    public_name = factory.Faker("name")
    credits = 0
