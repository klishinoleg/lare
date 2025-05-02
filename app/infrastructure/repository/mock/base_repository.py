from __future__ import annotations
from domain.abstract import EntityRepository
from abc import ABC
from typing import List
from domain.abstract import BaseEntity


class Table[E: BaseEntity]:
    def __init__(self) -> None:
        self.entities: dict[int, E] = {}
        self.counter: int = 0
        super().__init__()

    def clear(self) -> None:
        self.entities = {}
        self.counter = 0


class BaseMockRepository[E: BaseEntity](EntityRepository[E], ABC):
    """
    Base in-memory repository implementation for testing.

    This mock repository stores entities in a simple Python dictionary and
    simulates CRUD operations. It is useful for running unit tests without
    needing a real database connection.

    Type Parameters:
        E (BaseEntity): The type of entity this repository manages.

    Attributes:
        entities (dict[int, E]): In-memory storage of entities by their ID.
        counter (int): Auto-incrementing ID generator for new entities.

    Methods:
        get_by_id(id: int) -> E | None:
            Retrieve an entity by its unique ID.

        list() -> List[E]:
            Return a list of all stored entities.

        delete(id: int) -> bool:
            Remove an entity by ID. Returns True if deleted.

        save(entity: E) -> E | None:
            Insert or update an entity. Assigns a new ID if needed.
    """

    db: dict[str, Table] = {}

    def __init__(self) -> None:
        classname = self.__class__.__name__.lower()
        if classname not in self.db:
            self.db[classname] = Table()
        self.entities = self.db[classname].entities
        self.counter = self.db[classname].counter

    async def get_by_id(self, id: int) -> E | None:
        """
        Retrieve an entity by its ID.

        Args:
            id (int): The ID of the entity to retrieve.

        Returns:
            E | None: The entity if found, otherwise None.
        """
        return self.entities.get(id, None)

    async def list(self) -> List[E]:
        """
        List all stored entities.

        Returns:
            List[E]: All entities currently in the repository.
        """
        return list(self.entities.values())

    async def delete(self, id: int) -> bool:
        """
        Delete an entity by ID.

        Args:
            id (int): The ID of the entity to delete.

        Returns:
            bool: True if the entity was found and deleted, False otherwise.
        """
        return self.entities.pop(id, None) is not None

    async def save(self, entity: E) -> E | None:
        """
        Save or update an entity in memory.

        If the entity is new (no ID), it is assigned a new one.
        If it exists, it is updated.

        Args:
            entity (E): The entity to store.

        Returns:
            E | None: The stored entity.
        """
        if entity.id is None:
            self.counter += 1
            while self.entities.get(self.counter):
                self.counter += 1
            entity.id = self.counter
        self.entities[entity.id] = entity
        return entity
