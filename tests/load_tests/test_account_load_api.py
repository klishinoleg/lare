from tests.load_tests.abstract.base import BaseLoadTestAPI
from application.account.dtos import CreateAccountDTO
from tests.t_domain.entities.account import AccountFactory


class TestAccountLoadAPI(BaseLoadTestAPI):
    route = "/account"
    factory = AccountFactory
    init_create_dto = CreateAccountDTO
