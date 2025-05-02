from __future__ import annotations

from factory import Factory
import pytest
from abc import ABC
from typing import Type
from application.abstract.services.crud import BaseCRUDService
from application.access_control.services.user_creator_service import UserCreatorService
from application.account.services import AccountService
from core.enums.repository.types import RepositoryTypes
from domain.abstract import BaseEntity, EntityRepository, EntityNotFoundException, PermissionDenied
from domain.account.entities import AccountEntity
from domain.auth_profile.exceptions import AuthProfileAlreadyExistsError
from tests.t_domain.entities.account import AccountFactory
from core.config import settings


# Abstract base class for reusable CRUD service tests
class BaseCRUDServiceTest[E: BaseEntity, ER: EntityRepository, BCRUDS: BaseCRUDService, F: Factory](ABC):
    # Repository type to use (e.g. MOCK, TORTOISE, REDIS, etc.)
    init_repository_type: RepositoryTypes = RepositoryTypes.MOCK
    # Abstract repository class (interface) to be resolved via DI
    init_entity_repository: Type[ER]
    # Service class that implements CRUD logic
    init_service_type: Type[BCRUDS]
    # Factory method to generate test entities
    factory: Type[F]
    # Initialized service instance
    _service: BCRUDS
    _main_account: AccountEntity | None = None
    _field_for_update = "name"

    def __init_subclass__(cls, **kwargs: dict) -> None:
        settings.repository_type = cls.init_repository_type
        super().__init_subclass__(**kwargs)

    @pytest.fixture(autouse=True)
    def setup_func(self) -> None:
        """
        Automatically executed before each test.
        Initializes the service using the DIRepository and assigns the factory method.
        """
        self._service = self.init_service_type(
            self.init_repository_type,
            entity_repository_type=self.init_entity_repository
        )
        self._factory = self.factory

    @pytest.mark.asyncio
    async def test_create_one(self) -> None:
        """
        Test that a single entity can be created and retrieved by its ID.
        """
        entity = await self._get_fake_entity()
        created = await self._service.create(entity)
        assert created.id is not None
        fetched = await self._service.get_by_id(created.id)
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_create_multiple(self) -> None:
        """
        Test that multiple entities can be created and have unique IDs.
        """
        entities = [await self._service.create(await self._get_fake_entity()) for _ in range(10)]
        assert len(entities) == 10
        ids = [e.id for e in entities]
        assert len(set(ids)) == 10
        assert all(ids)

    @pytest.mark.asyncio
    async def test_update_entities(self) -> None:
        """
        Test updating existing entities and ensuring that ID cannot be changed.
        """
        created_entities = [await self._service.create(await self._get_fake_entity()) for _ in range(5)]
        for entity in created_entities:
            updated = await self._get_fake_entity()
            original_id = entity.id
            updated.id = original_id
            await self._service.update(updated, await self._get_account_entity(updated))
            fetched = await self._service.get_by_id(original_id)
            assert fetched.id == original_id
            assert fetched != entity  # ensures fields were updated

            # Try to update with invalid ID and expect it to be ignored or fail
            fetched.id = 999999
            setattr(fetched, self._field_for_update, getattr(entity, self._field_for_update))
            result = await self._service.update(fetched, await self._get_account_entity(updated))
            assert result is False or fetched.id != 999999

    @pytest.mark.asyncio
    async def test_list_entities(self) -> None:
        """
        Test that the service returns all created entities and all have unique IDs.
        """
        await self.test_create_multiple()
        all_entities = await self._service.list()
        assert len(all_entities) > 10
        ids = [e.id for e in all_entities]
        assert len(set(ids)) > 10
        assert all(ids)

    @pytest.mark.asyncio
    async def test_delete_entity(self) -> None:
        """
        Test deleting an entity, and ensure:
        - the entity is removed
        - repeated deletion raises EntityNotFoundException
        - accessing it afterward also raises EntityNotFoundException
        - list no longer contains the entity
        """
        entity = await self._service.create(await self._get_fake_entity())
        alive_entity = await self._service.create(await self._get_fake_entity())
        await self._service.delete(entity, await self._get_account_entity(entity))

        with pytest.raises(EntityNotFoundException):
            await self._service.delete(entity, await self._get_account_entity(entity))

        with pytest.raises(EntityNotFoundException):
            await self._service.get_by_id(entity.id)

        all_entities = await self._service.list()
        assert all(e.id != entity.id for e in all_entities)
        alive_fetched = await self._service.get_by_id(alive_entity.id)
        assert alive_fetched.id == alive_entity.id

    @pytest.mark.asyncio
    async def test_superuser(self) -> None:
        try:
            superuser = await UserCreatorService.create_superuser(username="superuser", password="passw",
                                                                  public_name="Super User",
                                                                  repository_type=self.init_repository_type)
        except AuthProfileAlreadyExistsError:
            superuser = await AccountService().get_by_username(username="superuser")
        entity = await self._service.create(await self._get_fake_entity())
        new_value = "New value"
        setattr(entity, self._field_for_update, new_value)
        updated_entity = await self._service.update(entity, superuser)
        assert getattr(updated_entity, self._field_for_update) == new_value
        await self._service.delete(entity, superuser)
        with pytest.raises(EntityNotFoundException):
            await self._service.get_by_id(entity.id)

    @pytest.mark.asyncio
    async def test_delete_entity_with_wrong_account(self) -> None:
        entity = await self._service.create(await self._get_fake_entity())
        wrong_account = await self._get_account_service().create(AccountFactory())
        with pytest.raises(PermissionDenied):
            await self._service.update(entity, wrong_account)
        with pytest.raises(PermissionDenied):
            await self._service.delete(entity, wrong_account)

    async def _get_main_account(self) -> AccountEntity:
        if not getattr(self, "_main_account", None):
            self._main_account = await self._get_account_service().create(AccountFactory())
        return self._main_account

    async def _get_account_entity(self, entity: E) -> AccountEntity:
        if isinstance(entity, AccountEntity):
            return entity
        return await self._get_main_account()

    async def _get_fake_entity(self, **kwargs: dict) -> E:
        return self.factory(**kwargs)  # type: ignore[return-value]

    def _get_account_service(self) -> AccountService:
        if isinstance(self._service, AccountService):
            return self._service
        if not getattr(self, "_account_service", None):
            self._account_service = AccountService(RepositoryTypes.MOCK)
        return self._account_service
