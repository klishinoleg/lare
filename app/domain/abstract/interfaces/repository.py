from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from domain.abstract.entity import E


class EntityRepository(ABC, Generic[E]):
    """
    Abstract base class for a repository that manages a specific domain entity.

    This interface defines the basic CRUD operations that all repository implementations
    should provide, regardless of the underlying storage mechanism (e.g., ORM, Redis, mock).

    Type Parameters:
        E: The type of the domain entity being managed.

    Methods:
        get_by_id(id: int) -> Optional[E]:
            Retrieve a single entity by its primary key.

        list() -> List[E]:
            Retrieve all stored entities.

        save(entity: E) -> E | None:
            Persist a new or updated entity.

        delete(id: int) -> bool:
            Remove an entity by its ID.
    """

    @classmethod
    def get_base_class_name(cls):
        """
        Returns the simplified class name without the 'Repository' suffix.

        Useful for identifying the related entity dynamically based on class naming.

        Returns:
            str: Base class name (e.g., 'Account' for 'AccountRepository').
        """
        return cls.__name__.replace('Repository', '')

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[E]:
        """
        Retrieve an entity by its unique identifier.

        Args:
            id (int): Primary key of the entity.

        Returns:
            Optional[E]: The found entity or None if not found.
        """
        ...

    @abstractmethod
    async def list(self) -> List[E]:
        """
        List all entities.

        Returns:
            List[E]: All stored entities of type E.
        """
        ...

    @abstractmethod
    async def save(self, entity: E) -> E | None:
        """
        Create or update an entity.

        Args:
            entity (E): The entity to persist.

        Returns:
            E | None: The saved entity, or None if save failed (e.g., update target not found).
        """
        ...

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """
        Delete an entity by its ID.

        Args:
            id (int): ID of the entity to delete.

        Returns:
            bool: True if deletion succeeded, False otherwise.
        """
        ...


# Generic type for working with repositories in a type-safe way
ER = TypeVar('ER', bound=EntityRepository)
