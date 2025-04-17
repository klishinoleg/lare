from enum import Enum


class RepositoryTypes(str, Enum):
    """
    Enumeration of available repository backends.

    This enum is used to indicate which implementation of a repository
    should be used for a given context. It supports switching between
    real databases, in-memory repositories, or test mocks.

    Attributes:
        TORTOISE: Tortoise ORM backend (PostgreSQL, SQLite, etc.).
        REDIS: Redis-based repository.
        SQLITE: Lightweight SQLite storage.
        MOCK: In-memory or mock repository for testing purposes.
    """
    TORTOISE = "Tortoise"
    REDIS = "Redis"
    SQLITE = "SQLite"
    MOCK = "Mock"
