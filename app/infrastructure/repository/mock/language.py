from domain.language.entities import LanguageEntity
from domain.language.interfaces.repository import LanguageRepository
from infrastructure.repository.mock.base_repository import BaseMockRepository


class MockLanguageRepository(BaseMockRepository[LanguageEntity], LanguageRepository):
    """
    In-memory mock implementation of LanguageRepository for testing purposes.

    Provides basic CRUD operations using a dictionary, useful for unit testing.
    """
    ...
