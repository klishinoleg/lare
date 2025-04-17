from locust import HttpUser, task, between
from tests.load_tests.test_account_load_api import TestAccountLoadAPI

account_loader = TestAccountLoadAPI()


class AccountUser(HttpUser):
    wait_time = between(0.1, 0.3)

    @task
    def create_account(self):
        self.client.post(account_loader.route + "/", json=account_loader.get_create_payload())
