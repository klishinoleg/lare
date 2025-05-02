import enum


class EventStreamingTypes(enum.Enum):
    REDIS = "redis"
    MOCK = "mock"
