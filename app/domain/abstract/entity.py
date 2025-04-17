from __future__ import annotations
from dataclasses import dataclass, asdict, field
from abc import ABC
from typing import Any


@dataclass
class BaseEntity(ABC):
    """
    Abstract base class for all domain entities.

    This class provides a common structure for all entities with an `id` field,
    utility methods, and safeguards to preserve immutability of primary keys.

    Attributes:
        id (int | None): Unique identifier for the entity. None if not yet persisted.

    Methods:
        to_dict(exclude_id: bool = False) -> dict:
            Converts the entity to a dictionary representation.
            Can optionally exclude the 'id' field.

        is_new() -> bool:
            Returns True if the entity has not been persisted yet (id is None).

        __setattr__:
            Prevents changing the `id` once it is set, ensuring identity immutability.
    """

    id: int | None = field(default=None)

    def to_dict(self, exclude_id: bool = False) -> dict:
        """
        Convert the entity to a dictionary.

        Args:
            exclude_id (bool): Whether to exclude the `id` from the result.

        Returns:
            dict: A dictionary representation of the entity.
        """
        d = asdict(self)
        if exclude_id:
            d.pop('id', None)
        return d

    def is_new(self) -> bool:
        """
        Check if the entity is new (i.e., not yet persisted).

        Returns:
            bool: True if the entity's id is None.
        """
        return self.id is None

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Prevent reassignment of 'id' after it is initially set.

        This ensures that the identity of an entity is immutable
        after creation or retrieval from storage.
        """
        if name == "id" and getattr(self, "id", None) is not None:
            return
        super().__setattr__(name, value)
