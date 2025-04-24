from infrastructure.payment.base import BasePaymentProvider
from infrastructure.payment.providers.telegram_stars import TelegramStarsProvider
from core.enums.payment.payment_service import PaymentService


class DIPayment:
    @staticmethod
    def get_provider(payment_service: PaymentService) -> BasePaymentProvider:
        if payment_service == PaymentService.TG_STARS:
            return TelegramStarsProvider()
        raise NotImplementedError(f"Payment service {payment_service} not implemented")
