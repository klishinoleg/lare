from enum import Enum


class EventTypes(Enum):
    ...


class ChapterEventTypes(EventTypes):
    CREATE_REQUESTED = "chapter.create.requested"
    TEXT_PROCESSED = "chapter.text.processed"
    WORDS_SAVED = "chapter.words.saved"
    CREATION_COMPLETED = "chapter.creation.completed"
    CREATION_ERROR = "chapter.creation.error"


class FinanceEventTypes(EventTypes):
    BILL_CREATED = "finance.bill.created"
    PAYMENT_CREATED = "finance.payment.created"
    PAYMENT_PAID = "finance.payment.paid"
    PAYMENT_CONFIRMED = "finance.payment.confirmed"
    BILL_SUCCESSFUL = "finance.bill.successful"
    PAYMENT_REFUNDED = "finance.payment.refunded"
    BILL_REFUNDED = "finance.bill.refunded"
    BILL_ERROR = "finance.bill.error"

    USAGE_CREATED = "finance.usage.created"
    USAGE_CANCELLED = "finance.usage.cancelled"
    USAGE_ERROR = "finance.usage.error"

    TRANSACTION_CREATED = "finance.transaction.created"
    TRANSACTION_ERROR = "finance.transaction.error"
