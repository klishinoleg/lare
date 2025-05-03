from __future__ import annotations
from abc import ABC
from typing import Optional, List, Type
from application.abstract.exceptions import RepositoryIsNotSet
from core.di.repository import DIRepository
from core.enums.repository.types import RepositoryTypes
from core.helpers.mixins.methods_worker import MethodWorkerMixin
from domain.abstract import BaseEntity, EntityCRUDService, EntityNotFoundException, EntityRepository
from domain.abstract.exceptions import NotDefinedRepositoryException, PDEXC, PermissionDenied
from application.abstract.dtos import BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemDTO, BaseItemsListDTO
from domain.access_role.enums.roles import AccessRole
from application.access_control.services import Accessor
from application.access_control.validators import OwnedByAccountValidator
from domain.account.entities import AccountEntity


class BaseCRUDService[E: BaseEntity, AR: EntityRepository, BIDTO: BaseItemDTO, BILDTO: BaseItemsListDTO,
                      BCIDTO: BaseCreateItemDTO, BUIDTO: BaseUpdateItemDTO](
    EntityCRUDService[E],
    MethodWorkerMixin[E],
    ABC
):
    """
    Abstract CRUD service base class with dynamic repository resolution.

    This class provides a reusable foundation for building business logic services
    that work with a single entity and a single repository.

    Responsibilities:
    - Manage CRUD operations with validation/modification hooks
    - Convert between DTOs and entities
    - Dynamically resolve the appropriate repository using DI
    - Serve as the core place for encapsulating business rules per entity

    This base class assumes that only **one repository** is needed per service.
    If multiple repositories are needed, use a custom service instead.

    Type parameters:
        E (BaseEntity): The entity managed by the CRUD service
    """

    # Repository configuration
    entity_repository_type: Type[AR] | None = None
    repository: AR | None = None
    repository_type: RepositoryTypes | None = RepositoryTypes.TORTOISE

    # Entity and DTO types
    entity_class: Type[E]
    entity_permission_denied_exception: PDEXC = PermissionDenied
    create_dto: Type[BCIDTO]
    list_dto: Type[BILDTO]
    item_dto: Type[BIDTO]
    update_dto: Type[BUIDTO]
    not_found_exception: Type[EntityNotFoundException]
    access_role: AccessRole = AccessRole.ADMINISTRATOR

    def __init__(
            self,
            repository_type: RepositoryTypes | None = None,
            entity_repository_type: Optional[Type[EntityRepository[E]]] = None
    ) -> None:
        """
        Initialize the service and resolve its repository using DI.

        Args:
            repository_type: Desired backend implementation (default is Tortoise).
            entity_repository_type: The abstract interface or base repo class.

        Raises:
            NotDefinedRepositoryException: If repository could not be resolved.
        """
        if entity_repository_type:
            self.entity_repository_type = entity_repository_type
        self.repository_type = repository_type
        if not self.repository and self.entity_repository_type:
            self.set_repository(self.repository_type)
        if not self.repository:
            raise NotDefinedRepositoryException()
        self._set_acces_control_validators()

    def _set_acces_control_validators(self) -> None:
        Accessor.register(self.entity_class, OwnedByAccountValidator(), self.entity_permission_denied_exception)

    def set_repository(self, repository_type: RepositoryTypes) -> None:
        """
        Set or switch the repository implementation.

        Args:
            repository_type: Type of repository backend to use.
        """
        self.repository_type = repository_type
        self.repository = DIRepository.get_repository(
            self.entity_repository_type,
            self.repository_type
        )()

    def from_create_dto(self, data: BCIDTO) -> E:
        """
        Convert Create DTO to entity.

        Args:
            data: Incoming DTO.

        Returns:
            E: Constructed entity.
        """
        return self.entity_class(**data.model_dump())

    @staticmethod
    def from_update_dto(entity: E, data: BUIDTO) -> E:
        """
        Apply update DTO fields to an existing entity.

        Args:
            entity: Existing entity.
            data: DTO with update fields.

        Returns:
            E: Updated entity instance.
        """
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, key, value)
        return entity

    def to_item_dto(self, entity: E) -> BIDTO:
        """
        Convert entity to detailed DTO.
        """
        return self.item_dto.create_from_dict(entity.to_dict())

    def to_list_dto(self, entities: list[E]) -> list[BILDTO]:
        """
        Convert list of entities to list DTO.
        """
        return [self.list_dto.create_from_dict(e.to_dict()) for e in entities]

    async def create(self, entity: E) -> E:
        """
        Validate and create a new entity.

        Runs _create_validate__ and _create_modificate__ methods before saving.

        Returns:
            E: Saved entity.
        """
        if not self.repository:
            raise RepositoryIsNotSet()
        await self._run_methods("_create_validate__", entity)
        new_entity = await self._modificate_entity("_create_modificate__", entity)
        return await self.repository.save(new_entity)

    async def get_by_id(self, id: int) -> Optional[E]:
        """
        Retrieve entity by ID or raise exception.

        Args:
            id: Entity ID.

        Raises:
            not_found_exception if not found.
        """
        if not self.repository:
            raise RepositoryIsNotSet()
        entity = await self.repository.get_by_id(id)
        if entity is None:
            raise self.not_found_exception
        return entity

    async def list(self) -> List[E]:
        """
        List all entities.
        """
        if not self.repository:
            raise RepositoryIsNotSet()
        return await self.repository.list()

    async def update(self, entity: E, account: AccountEntity | None = None, is_system: bool = False) -> E:
        """
        Validate and update an existing entity.

        Runs _update_validate__ and _update_modificate__ methods before saving.
        """
        if not self.repository:
            raise RepositoryIsNotSet()
        if not is_system:
            await Accessor.or_raise(entity, account, self.access_role, self.repository_type)
            await self._run_methods("_update_validate__", entity)
        new_entity = await self._modificate_entity("_update_modificate__", entity)
        saved_entity = await self.repository.save(new_entity)
        if not saved_entity:
            raise self.not_found_exception
        return saved_entity

    @staticmethod
    async def _update_modificate__set_update_at(entity: E) -> E:
        """
        Internal method to update timestamps if the entity supports it.
        """
        if hasattr(entity, "set_update_now"):
            return getattr(entity, "set_update_now")()
        return entity

    async def delete(self, entity: E, account: AccountEntity | None = None, is_system: bool = False) -> None:
        """
        Delete entity by ID or raise not_found_exception.
        """
        if not self.repository:
            raise RepositoryIsNotSet()
        if not is_system:
            await Accessor.or_raise(entity, account, self.access_role, self.repository_type)
        if not await self.repository.delete(entity.id):
            raise self.not_found_exception
