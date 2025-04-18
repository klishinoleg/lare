import os
import shutil
import types
from abc import ABC
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from starlette.routing import Router

from application.access_control.services.user_creator_service import UserCreatorService
from application.account.services import AccountService
from application.auth.dtos.password import PasswordLoginDTO
from application.language.dtos import LanguageCreateDTO
from core.config import settings
from domain.account.entities import AccountEntity
from domain.account.exceptions import AccountAlreadyExistsError
from infrastructure.auth.dtos.telegram import TelegramProviderDataDTO
from application.auth.dtos import AuthResponseDTO
from infrastructure.loaders.load_languages import load_languages_init_entities
from tests.t_infrastructure.auth.factory.password import PasswordLoginDTOFactory
from tests.t_infrastructure.auth.factory.telegram import create_fake_telegram_provider_data
from unittest.mock import patch
from importlib import import_module, reload


class SuperUserDTO(BaseModel):
    account: AccountEntity
    password: str


class BaseClientTest(ABC):
    route_auth_telegram = "/auth/telegram/"
    route_me = "/auth/me/"
    route_profiles = "/auth/profiles/"
    route_auth_register = "/auth/register/"
    route_auth_login = "/auth/login/"
    route_auth_change_password = "/auth/change_password/"

    @staticmethod
    def _get_auth_telegram_provider_data(valid: bool = True) -> TelegramProviderDataDTO:
        fake_init_data = create_fake_telegram_provider_data()
        if valid is False:
            fake_init_data.init_data = fake_init_data.init_data.replace("hash=", "hash=a")
        return fake_init_data

    @pytest.fixture(autouse=True, scope="session")
    def set_config(self) -> None:
        settings.database_url = "sqlite://test_db.sqlite3"

    @pytest.fixture(scope="session")
    def client(self) -> Generator:
        def get_extended_auth_router() -> Router:
            original_auth = import_module("interfaces.fast_api.routers.auth")
            router = original_auth.router

            @router.get("/test/create_superuser/")
            async def create_super_user() -> SuperUserDTO:
                try:
                    superuser = await UserCreatorService.create_superuser("superuser",
                                                                          "passw",
                                                                          public_name="Super User")
                except AccountAlreadyExistsError:
                    superuser = await AccountService().get_by_username("superuser")
                return SuperUserDTO(account=superuser, password="passw")

            return router

        fake_auth_module = types.ModuleType("auth")
        setattr(fake_auth_module, "router", get_extended_auth_router())
        with patch.dict("sys.modules", {"interfaces.fast_api.routers.auth": fake_auth_module}):
            import interfaces.fast_api.main as main_module
            reload(main_module)
            with TestClient(main_module.app) as c:
                yield c
        db_url = settings.database_url.replace("sqlite://", "")
        try:
            if os.path.exists(db_url):
                os.remove(db_url)
            shutil.rmtree(settings.get_upload_dir(), ignore_errors=True)
        except PermissionError:
            ...

    @pytest.fixture(scope="module")
    def auth_user_data(self, client: TestClient) -> AuthResponseDTO:
        fake_user_telegram_data = self._get_auth_telegram_provider_data()
        auth_response = client.post(self.route_auth_telegram, json=fake_user_telegram_data.model_dump())
        return AuthResponseDTO.model_validate(auth_response.json())

    def _get_superuser_token(self, client: TestClient) -> str:
        superuser_response = client.get("/auth/test/create_superuser/")
        assert superuser_response.status_code == 200
        superuser_data = superuser_response.json()
        superuser = AccountEntity(**superuser_data.get("account"))
        password = superuser_data.get("password")
        login_dto: PasswordLoginDTO = PasswordLoginDTOFactory(
            username=superuser.username,
            password=password
        )
        login_response = client.post(self.route_auth_login, json=login_dto.model_dump())
        assert login_response.status_code == 200
        return login_response.json().get("token")

    def _create_languages(self, client: TestClient, limit: int = 10) -> None:
        language_route = "/language"
        token = self._get_superuser_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        assert token
        languages = load_languages_init_entities(limit)
        lang_create_dto = None
        for language in languages:
            lang_create_dto = LanguageCreateDTO.model_validate(language.to_dict())
            client.post(language_route, json=lang_create_dto.model_dump(), headers=headers)
        if lang_create_dto:
            assert client.post(language_route, json=lang_create_dto.model_dump()).status_code == 403
        assert len(client.get(language_route).json()) >= limit
