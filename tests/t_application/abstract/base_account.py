from copy import deepcopy
from typing import TYPE_CHECKING
import pytest
from application.auth.dtos import AuthResponseDTO
from application.auth.services.auth_via_profile import AuthViaProfileService
from core.config import settings
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.repository.types import RepositoryTypes
from domain.auth_profile.enums import AuthProviderType
from infrastructure.auth.dtos.telegram import TelegramAuthInitDataDTO
from core.registrators.init_auth_providers import register_auth_providers
from infrastructure.broker.mock.publisher import MockPublisher
from tests.t_infrastructure.auth.factory.telegram import create_fake_telegram_provider_data
from application.abstract.events import EventTypes

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent


class BaseAccountTest[BE: "BaseEvent", ET: EventTypes]:

    @pytest.fixture(autouse=True, scope="session")
    def config(self) -> None:
        settings.repository_type = RepositoryTypes.MOCK
        settings.event_broker_type = EventBrokerTypes.MOCK

    @pytest.fixture(scope="function")
    def auth_init_data(self) -> TelegramAuthInitDataDTO:
        register_auth_providers()
        settings.secret_key = "test_secret_key"
        fake_init_data = create_fake_telegram_provider_data()
        return TelegramAuthInitDataDTO(
            provider_type=AuthProviderType.TELEGRAM,
            provider_data=fake_init_data,
        )

    @pytest.fixture(scope="function")
    async def auth_response(self, auth_init_data: TelegramAuthInitDataDTO) -> AuthResponseDTO:
        return await AuthViaProfileService().authenticate(auth_init_data)

    @staticmethod
    def print_events(hide_trace_back: bool = False) -> None:
        for n, (event, payload) in enumerate(MockPublisher.get_events()):
            print(f"------------------ {n + 1} -------------------")
            print(event)
            for k, v in payload.model_dump().items():
                if k != "traceback" or not hide_trace_back:
                    print(k, ":::", v)

    @staticmethod
    def get_events() -> list[tuple[ET, BE]]:
        events = deepcopy(MockPublisher.get_events())
        MockPublisher.clear_events()
        return events

    @classmethod
    def check_events(cls, *args: tuple) -> list[tuple[ET, BE]]:
        events = cls.get_events()
        line = args
        assert len(events) == len(line)
        for i, (event, payload) in enumerate(events):
            assert event == line[i][0], f"event {i} must be {event}"
            if line[i][1] is not None:
                for k, v in line[i][1].items():
                    assert getattr(payload, k), f"{k=} not in {payload=}"
                    assert v == getattr(payload, k), f"{v=} not equal to {getattr(payload, k)=}"
        return events
