import factory
from faker import Faker

from application.auth.dtos.password import PasswordRegistrationDTO, PasswordLoginDTO, ChangePasswordDTO, \
    PasswordRegistrationInitDataDTO, PasswordLoginInitDataDTO, ChangePasswordInitDataDTO
from domain.auth_profile.enums import AuthProviderType

fake = Faker()


class PasswordRegistrationDTOFactory(factory.Factory):
    class Meta:
        model = PasswordRegistrationDTO

    password = factory.LazyFunction(lambda: fake.password(length=12))
    repeat_password = factory.LazyAttribute(lambda obj: obj.password)
    username = factory.LazyFunction(lambda: fake.user_name().lower())
    language_code = factory.LazyFunction(lambda: fake.language_code())
    public_name = factory.LazyFunction(lambda: fake.first_name())


class PasswordLoginDTOFactory(factory.Factory):
    class Meta:
        model = PasswordLoginDTO

    username = factory.Faker("user_name")
    password = factory.Faker("password")


class ChangePasswordDTOFactory(factory.Factory):
    class Meta:
        model = ChangePasswordDTO

    password = factory.LazyFunction(lambda: fake.password(length=12))
    repeat_password = factory.LazyAttribute(lambda obj: obj.password)


class PasswordRegistrationInitDataDTOFactory(factory.Factory):
    class Meta:
        model = PasswordRegistrationInitDataDTO

    provider_type = AuthProviderType.PASSWORD
    provider_data = factory.SubFactory(PasswordRegistrationDTOFactory)


class PasswordLoginInitDataDTOFactory(factory.Factory):
    class Meta:
        model = PasswordLoginInitDataDTO

    provider_type = AuthProviderType.PASSWORD
    provider_data = factory.SubFactory(PasswordLoginDTOFactory)


class ChangePasswordInitDataDTOFactory(factory.Factory):
    class Meta:
        model = ChangePasswordInitDataDTO

    provider_type = AuthProviderType.PASSWORD
    provider_data = factory.SubFactory(ChangePasswordDTOFactory)
