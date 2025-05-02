from httpx import AsyncClient
from starlette import status
from core.datatypes.action_responses import ActionResponse
from tests.t_interfaces.abstract.base_client import BaseClientTest
import pytest


class TestFinance(BaseClientTest):
    transaction_route = "/transaction"
    start_bonus_route = transaction_route + "/start_bonus/"

    @pytest.mark.asyncio
    async def test_start_bonus(self, client: AsyncClient) -> None:
        fake_user_tg_data = self._get_auth_telegram_provider_data()
        auth_response = await client.post(self.route_auth_telegram, json=fake_user_tg_data.model_dump())
        assert auth_response.status_code == 200
        data = auth_response.json()
        start_bonus_response = await client.post(self.start_bonus_route, json=data,
                                                 headers=self._get_auth_headers(data.get("token")))
        assert start_bonus_response.status_code == status.HTTP_200_OK
        action_response = ActionResponse.model_validate(start_bonus_response.json())
        assert action_response.success is True
        start_bonus_retry_response = await client.post(self.start_bonus_route, json=data,
                                                       headers=self._get_auth_headers(data.get("token")))
        assert start_bonus_retry_response.status_code == status.HTTP_403_FORBIDDEN
        start_bonus_not_auth_response = await client.post(self.start_bonus_route, json=data, )
        assert start_bonus_not_auth_response.status_code == status.HTTP_403_FORBIDDEN
