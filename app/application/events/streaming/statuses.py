import enum


class StreamingStatuses(enum.Enum):
    PENDING = "pending"
    AI_REQUEST = "ai_request"
    PROCESSING = "processing"
    FINANCE = "finance"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
