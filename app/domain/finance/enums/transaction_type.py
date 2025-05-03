from enum import Enum


class TransactionType(str, Enum):
    AI_USAGE = "ai_usage"
    AI_USAGE_CANCEL = "ai_usage_cancel"
    START_BONUS = "start_bonus"
    PAYMENT = "payment"
    MANUAL = "manual"
    REFUND = "refund"
    REFERRAL = "ref"
    REFUND_REFERRAL = "ref_ref"
