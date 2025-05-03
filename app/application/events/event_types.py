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
    BILL_PAYMENT = "finance.bill.payment"
    BILL_PAID = "finance.bill.paid"
    BILL_CONFIRMED = "finance.bill.confirmed"
    BILL_REFUNDED = "finance.bill.refunded"
    BILL_ERROR = "finance.bill.error"

    USAGE_CREATED = "finance.usage.created"
    USAGE_CANCELLED = "finance.usage.cancelled"
    USAGE_ERROR = "finance.usage.error"

    TRANSACTION_START_BONUS = "finance.transaction.startbonus"
    TRANSACTION_CREATED = "finance.transaction.created"
    TRANSACTION_ERROR = "finance.transaction.error"
