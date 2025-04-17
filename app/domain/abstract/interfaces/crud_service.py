from abc import ABC, abstractmethod
from typing import Generic, Optional, List, TypeVar
from ..entity import E


class EntityCRUDService(ABC, Generic[E]):
    """
    Abstract base class for defining CRUD operations for domain entities.

    This interface should be implemented by service classes that handle the core
    application logic for creating, retrieving, updating, and deleting domain entities.

    Type Parameters:
        E: The type of domain entity managed by the service.

    Methods:
        create(entity: E) -> bool:
            Create a new entity in the system.

        get_by_id(id: int) -> Optional[E]:
            Retrieve a single entity by its ID.

        list() -> List[E]:
            Retrieve all available entities.

        update(entity: E) -> bool:
            Update an existing entity.

        delete(id: int) -> bool:
            Delete an entity by its ID.
    """

    @abstractmethod
    async def create(self, entity: E) -> E:
        """
        Persist a new entity.

        Args:
            entity (E): The entity to be created.

        Returns:
            bool: True if creation was successful.
        """
        ...

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[E]:
        """
        Retrieve an entity by its unique identifier.

        Args:
            id (int): The ID of the entity.

        Returns:
            Optional[E]: The found entity, or None if not found.
        """
        ...

    @abstractmethod
    async def list(self) -> List[E]:
        """
        List all entities of this type.

        Returns:
            List[E]: A list of all stored entities.
        """
        ...

    @abstractmethod
    async def update(self, entity: E, account: E) -> E:
        """
        Update an existing entity.

        Args:
            entity (E): The entity with updated values.
            :param entity:
            :param account:
        Returns:
            bool: True if the update was successful.
        """
        ...

    @abstractmethod
    async def delete(self, entity: E, account: E) -> bool:
        """
        Delete an entity by its ID.

        Args:
            :param entity:
            :param account:
        Returns:
            bool: True if the entity was deleted.
        """
        ...


# Type variable for referencing any subclass of EntityCRUDService
ECRUDS = TypeVar('ECRUDS', bound=EntityCRUDService)
