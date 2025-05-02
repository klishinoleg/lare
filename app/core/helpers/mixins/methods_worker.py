import asyncio
import copy
from typing import Callable

from domain.abstract import BaseEntity


class MethodWorkerMixin[E: BaseEntity]:
    """
    Mixin class to dynamically discover and invoke methods by prefix.

    This utility is commonly used in domain or application services to
    modularize logic by naming conventions (e.g., `_create_validate__*`, `_update_modify__*`).

    Features:
    - Caches methods starting with a given prefix.
    - Executes all such methods sequentially (sync or async).
    - Can be used to transform or validate entities before processing.

    Example usage:
        - `_create_validate__check_username`
        - `_update_modify__normalize_fields`

    Methods:
        _get_methods_by_start_with(str) → dict[str, Callable]:
            Returns all callable methods starting with a given prefix.

        _run_methods(str, *args) → None:
            Calls each matched method with the given arguments.
            Supports both sync and async methods.

        _modificate_entity(str, entity: E) → E:
            Applies all matched methods to modify the entity.
            Each method receives and must return an updated entity.
    """

    def _get_methods_by_start_with(self, start_with: str) -> dict[str, Callable]:
        """
        Get all methods that start with a given prefix, cached per prefix.

        Args:
            start_with (str): The prefix to filter method names by.

        Returns:
            dict[str, Callable]: Mapping of method names to method objects.
        """
        if not hasattr(self, '__start_with_methods_cache'):
            self.__start_with_methods_cache: dict = {}
        if self.__start_with_methods_cache.get(start_with) is None:
            self.__start_with_methods_cache[start_with] = set(
                attr_name
                for attr_name in dir(self)
                if attr_name.startswith(start_with) and callable(getattr(self, attr_name))
            )
        return {k: getattr(self, k) for k in self.__start_with_methods_cache[start_with]}

    async def _run_methods(self, start_with: str, *args: tuple) -> None:
        """
        Run all methods starting with the given prefix and pass *args to them.

        Args:
            start_with (str): Method name prefix to match.
            *args: Arguments passed to each matched method.
        """
        for attr_name, method in self._get_methods_by_start_with(start_with).items():
            result = method(*args)
            if asyncio.iscoroutine(result):
                await result

    async def _modificate_entity(self, start_with: str, entity: E) -> E:
        """
        Apply all modification methods to an entity in sequence.

        Args:
            start_with (str): Prefix to identify modifier methods.
            entity (E): The entity instance to transform.

        Returns:
            E: Modified entity after applying all prefix-matched methods.
        """
        new_entity = copy.copy(entity)
        for attr_name, method in self._get_methods_by_start_with(start_with).items():
            new_entity = method(new_entity)
            if asyncio.iscoroutine(new_entity):
                new_entity = await new_entity
        return new_entity
