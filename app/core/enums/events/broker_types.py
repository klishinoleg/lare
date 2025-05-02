from enum import Enum


class EventBrokerTypes(Enum):
    KAFKA = "kafka"
    CELERY = "celery"
    MOCK = "mock"
