from __future__ import annotations
from importlib import import_module
from typing import Type, cast

from core.helpers.funcs.strings import camel_to_snake
from domain.abstract import EntityRepository
from core.enums.repository.types import RepositoryTypes


class DIRepository[ER: EntityRepository]:
    repositories: dict[str, dict[str, Type[ER]]] = {}

    @classmethod
    def get_repository(cls,
                       entity_repository: Type[ER],
                       repository_type: RepositoryTypes = RepositoryTypes.TORTOISE) -> Type[ER]:
        """
        Dynamic Repository Resolver
        ---------------------------

        This module provides a dynamic repository resolution mechanism based on a strict file structure convention.

        Goal:
        Instead of importing repositories manually for each domain/module, we dynamically resolve and load them at runtime
        based on the domain's base name and the repository type (e.g., Tortoise, Redis, SQLite).

        Directory Convention:
        All repository implementations must follow this directory and naming structure:

        infrastructure/
        └── repository/
            └── {type}/                      # Type of repository, e.g., tortoise, redis
                └── {entity}.py                # Entity/domain name, lowercase (e.g., "account")

        For example:
        - infrastructure/repository/tortoise/account/__init__.py
        - Class inside: `from .repository import TortoiseAccountRepository`

        Naming Convention:
        - Class name must be: `{Type}{Entity}Repository`
          - e.g. "TortoiseAccountRepository"
        - Module path is constructed dynamically using:
          - repository type: e.g. "tortoise"
          - base repository name from interface: e.g. "account"

        Usage:
        The `get_repository()` method will:
        1. Get the base name from the interface (e.g. "account")
        2. Get the repository type (e.g. "tortoise")
        3. Construct import path and class name
        4. Import and cache the repository class

        Fails loudly:
        If the module or class is not found, ImportError is raised with an informative message.
        This avoids silent misconfiguration and ensures reliable resolution.

        """
        base_repository_name = entity_repository.get_base_class_name()
        type_str = repository_type.value
        if type_str not in cls.repositories:
            cls.repositories[type_str] = {}
        if base_repository_name not in cls.repositories[type_str]:
            class_name = f"{type_str}{base_repository_name}Repository"
            module_path = f"infrastructure.repository.{type_str.lower()}.{camel_to_snake(base_repository_name)}"
            try:
                module = import_module(module_path)
                cls.repositories[type_str][base_repository_name] = getattr(module, class_name)
            except ModuleNotFoundError as e:
                raise ImportError(
                    f"Repository module '{module_path}' not found for base='{base_repository_name}', type='{type_str}'"
                ) from e
            except AttributeError as e:
                raise ImportError(
                    f"Repository class '{class_name}' not found in module '{module_path}'"
                ) from e
        return cast(Type[ER], cls.repositories[type_str][base_repository_name])
