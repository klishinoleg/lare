from enum import Enum


class PaymentService(str, Enum):
    TG_STARS = "tgstars"
    MANUAL = "manual"
