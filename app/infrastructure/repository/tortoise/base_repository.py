from __future__ import annotations
from domain.abstract import EntityRepository, BaseEntity
from abc import ABC, abstractmethod
from typing import List, Type, Callable, Any
from .models.abstract import AbstractModel
from core.db import get_master_connection, get_slave_connection


class BaseTortoiseRepository[E: BaseEntity, TM: AbstractModel](EntityRepository[E], ABC):
    """
    Abstract base repository for implementing domain entity persistence using Tortoise ORM.

    This class defines standard CRUD operations and expects the subclass to provide:
    - the Tortoise ORM model class (`model`)
    - a method to convert ORM models to domain entities (`to_entity`)

    It is designed to be subclassed per entity, allowing reuse of Tortoise logic across models.

    Type Parameters:
        E: Domain entity type (must inherit from BaseEntity).
        TM: Tortoise ORM model type (must inherit from AbstractModel).

    Methods:
        get_by_id(id: int) -> E | None:
            Retrieve an entity by its primary key.

        list() -> List[E]:
            Retrieve all entities from the model.

        delete(id: int) -> bool:
            Delete a record by ID.

        save(entity: E) -> E | None:
            Insert or update an entity in the database.
    """

    _use_master: bool = False

    def __init__(self, *args: Any, use_master: bool = False, **kwargs: Any) -> None:
        self._use_master = use_master
        super().__init__(*args, **kwargs)

    @staticmethod
    def read(use_master: bool = False) -> Callable:
        def decorator(func: Callable) -> Callable:
            async def wrapper(self: Any, *args: tuple, **kwargs: dict) -> Any:
                connection = get_master_connection() if use_master or self._use_master else get_slave_connection()
                async with connection.acquire_connection():
                    return await func(self, *args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def write() -> Callable:
        def decorator(func: Callable) -> Callable:
            async def wrapper(self: Any, *args: tuple, **kwargs: dict) -> Any:
                connection = get_master_connection()
                async with connection.acquire_connection():
                    return await func(self, *args, **kwargs)

            return wrapper

        return decorator

    @property
    @abstractmethod
    def model(self) -> Type[TM]:
        """
        Returns the Tortoise ORM model class associated with this repository.

        Returns:
            Type[TM]: A Tortoise ORM model class.
        """
        ...

    @staticmethod
    @abstractmethod
    async def to_entity(o: TM) -> E:
        """
        Convert a Tortoise ORM model instance to a domain entity.

        Args:
            o (TM): An ORM model object.

        Returns:
            E: Corresponding domain entity.
        """
        ...

    @read()
    async def get_by_id(self, id: int) -> E | None:
        """
        Retrieve an entity by its ID.

        Args:
            id (int): Primary key of the entity.

        Returns:
            E | None: Found entity or None if not found.
        """
        record = await self.model.get_or_none(id=id)
        return await self.to_entity(record) if record else None

    @read()
    async def list(self) -> List[E]:
        """
        Retrieve all entities from the database.

        Returns:
            List[E]: A list of all entities.
        """
        records = await self.model.all()
        return [await self.to_entity(r) for r in records]

    @write()
    async def delete(self, id: int) -> bool:
        """
        Delete an entity by ID.

        Args:
            id (int): Primary key of the entity to delete.

        Returns:
            bool: True if deleted, False if not found.
        """
        o = await self.model.get_or_none(id=id)
        if not o:
            return False
        await o.delete()
        return True

    @write()
    async def save(self, entity: E) -> E | None:
        """
        Save (create or update) an entity to the database.

        Args:
            entity (E): The domain entity to persist.

        Returns:
            E | None: The saved entity, or None if update target was not found.
        """
        if entity.id is None:
            o = await self.model(**entity.to_dict(exclude_id=True))
        else:
            record = await self.model.get_or_none(id=entity.id)
            if record is None:
                return None
            o = record  # type: ignore[assignment]
            o.update_from_dict(entity.to_dict())
        await o.save()
        saved_entity = await self.to_entity(o)
        return saved_entity
