from typing import TypeVar, Type, Dict

from core.enums.payment.payment_service import PaymentService
from infrastructure.payment.base import BasePaymentProvider
from infrastructure.payment.providers.telegram_stars import TelegramStarsProvider
from infrastructure.payment.providers.mock import MockPaymentProvider
from infrastructure.payment.providers.manual import ManualPaymentProvider

BPP = TypeVar("BPP", bound=BasePaymentProvider)


class DIPayment:
    _providers: Dict[PaymentService, Type[BasePaymentProvider]] = {
        PaymentService.TG_STARS: TelegramStarsProvider,
        PaymentService.MOCK: MockPaymentProvider,
        PaymentService.MANUAL: ManualPaymentProvider,
    }

    @classmethod
    def register(cls, service: PaymentService, provider_cls: Type[BasePaymentProvider]) -> None:
        cls._providers[service] = provider_cls

    @classmethod
    def get_provider(cls, service: PaymentService) -> BasePaymentProvider:
        try:
            return cls._providers[service]()
        except KeyError:
            raise NotImplementedError(f"Payment service {service} not registered")
