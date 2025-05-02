from httpx import AsyncClient
from application.auth.dtos.password import PasswordRegistrationDTO, PasswordLoginDTO, ChangePasswordDTO
from domain.auth_profile.enums import AuthProviderType
from tests.t_interfaces.abstract.base_client import BaseClientTest
import pytest
from tests.t_infrastructure.auth.factory.password import (
    PasswordRegistrationDTOFactory, PasswordLoginDTOFactory, ChangePasswordDTOFactory
)


class TestApiAuth(BaseClientTest):

    @pytest.mark.asyncio
    async def test_telegram_auth_and_me_data(self, client: AsyncClient) -> None:
        fake_user_tg_data = self._get_auth_telegram_provider_data()
        auth_response = await client.post(self.route_auth_telegram, json=fake_user_tg_data.model_dump())
        assert auth_response.status_code == 200
        auth_data = auth_response.json()
        token = auth_data.get("token")
        account = auth_data.get("account")
        me_response = await client.get(self.route_me, headers={"Authorization": f"Bearer {token}"})
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["id"] == account["id"]
        profiles_response = await client.get(self.route_profiles, headers={"Authorization": f"Bearer {token}"})
        assert profiles_response.status_code == 200
        profile_data = profiles_response.json()
        telegram_profile = next(
            (p for p in profile_data if p.get("provider_type") == AuthProviderType.TELEGRAM.value),
            None
        )
        assert telegram_profile is not None
        assert telegram_profile.get("language_code") == fake_user_tg_data.init_data_unsafe.user.language_code

    @pytest.mark.asyncio
    async def test_password_register_login_me_change_password(self, client: AsyncClient) -> None:
        registration_init_dto: PasswordRegistrationDTO = PasswordRegistrationDTOFactory()
        register_response = await client.post(self.route_auth_register, json=registration_init_dto.model_dump())
        assert register_response.status_code == 200
        register_data = register_response.json()
        token = register_data["token"]
        account = register_data["account"]

        me_response = await client.get(self.route_me, headers={"Authorization": f"Bearer {token}"})
        assert me_response.status_code == 200
        assert me_response.json()["username"] == registration_init_dto.username

        profiles_response = await client.get(self.route_profiles, headers={"Authorization": f"Bearer {token}"})
        assert profiles_response.status_code == 200
        assert any(p["provider_type"] == AuthProviderType.PASSWORD.value for p in profiles_response.json())

        login_init_dto: PasswordLoginDTO = PasswordLoginDTOFactory(
            username=registration_init_dto.username,
            password=registration_init_dto.password
        )
        login_response = await client.post(self.route_auth_login, json=login_init_dto.model_dump())
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data["account"]["id"] == account["id"]

        change_password_init_dto: ChangePasswordDTO = ChangePasswordDTOFactory()
        change_response = await client.post(
            self.route_auth_change_password,
            json=change_password_init_dto.model_dump(),
            headers={"Authorization": f"Bearer {token}"}
        )
        assert change_response.status_code == 200
        changed_data = change_response.json()
        assert changed_data["account"]["id"] == account["id"]

        new_login_dto: PasswordLoginDTO = PasswordLoginDTOFactory(
            username=registration_init_dto.username,
            password=change_password_init_dto.password
        )
        new_login_response = await client.post(self.route_auth_login, json=new_login_dto.model_dump())
        assert new_login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_superuser_create_languages(self, client: AsyncClient) -> None:
        await self._create_languages(client)
