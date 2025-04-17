# domain/access_control/services/authorizer.py
from __future__ import annotations

from collections import defaultdict

from core.di.repository import DIRepository
from core.enums.repository.types import RepositoryTypes
from core.messages.exceptions import GetExMessages
from domain.abstract import BaseEntity, E, PermissionDenied
from domain.access_role.enums.roles import AccessRole
from domain.access_role.interfaces.repository import AccessRoleRepository
from domain.account.entities import AccountEntity
from domain.access_role.interfaces.validator import BaseAccessValidator, BAL


class Accessor:
    """
    Universal access control service for domain entities.

    Allows registering validators per entity type and checking user access.
    """

    _validators: dict[type[BaseEntity], list[BAL]] = defaultdict(list)
    _exceptions: dict[type[BaseEntity], type[PermissionDenied]] = {}
    role_repository: AccessRoleRepository = None

    @classmethod
    async def has_role(cls, account: AccountEntity, role: AccessRole) -> bool:
        if cls.role_repository is None:
            return False
        return await cls.role_repository.has_role(account.id, role)

    @classmethod
    async def is_superuser(cls, account: AccountEntity) -> bool:
        return await cls.has_role(account, AccessRole.SUPERUSER)

    @classmethod
    def register(
            cls,
            entity_type: type[E],
            validator: BAL,
            exception: type[PermissionDenied] | None = None
    ) -> None:
        """
        Register a validator and optional exception class for a given entity type.

        Args:
            entity_type (type): The type of entity.
            validator (BaseAccessValidator): The validator instance.
            exception (type | None): Optional exception to raise on denied access.
        """
        cls._validators[entity_type].append(validator)
        if exception:
            cls._exceptions[entity_type] = exception

    @classmethod
    async def can_edit(cls,
                       entity: E,
                       account: AccountEntity,
                       access_role: AccessRole = AccessRole.ADMINISTRATOR
                       ) -> bool:
        """
        Check whether the given user has access to edit the given entity.

        Returns:
            bool: True if access is granted, otherwise False.
        """
        if await cls.has_role(account, access_role):
            return True
        validators = cls._validators.get(type(entity))
        if not validators:
            return False
        if len(cls._validators.get(type(entity))) == 0:
            return True
        for validator in validators:
            if await validator.has_access(entity, account):
                return True
        return False

    @classmethod
    async def or_raise(cls, entity: E, account: AccountEntity,
                       access_role: AccessRole = AccessRole.ADMINISTRATOR,
                       repository_type: RepositoryTypes = RepositoryTypes.TORTOISE
                       ) -> None:
        """
        Check access and raise exception if access is denied.

        Raises:
            PermissionDenied or registered exception.
        """
        if not cls.role_repository:
            cls.role_repository = DIRepository.get_repository(AccessRoleRepository, repository_type)()
        if not await cls.can_edit(entity, account, access_role):
            exc = cls._exceptions.get(type(entity), PermissionDenied)
            raise exc(GetExMessages.permision_denied(entity, account))

    @classmethod
    async def set_repo(cls, repository_type: RepositoryTypes = RepositoryTypes.TORTOISE) -> None:
        cls.role_repository = DIRepository.get_repository(AccessRoleRepository, repository_type)()
