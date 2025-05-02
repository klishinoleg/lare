from enum import Enum


class DeduplicatorTypes(str, Enum):
    REDIS = "redis"
    FILE = "file"
