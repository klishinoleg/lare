from __future__ import annotations

from enum import Enum
from typing import Type, Optional

from fastapi import APIRouter, Depends, Request, HTTPException, status
from starlette.responses import Response

from application.access_control.services import Accessor
from application.abstract.services.crud import EntityCRUDService
from application.abstract.dtos import BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemDTO, BaseItemsListDTO
from interfaces.fast_api.routers.abstract.pagination import paginate, PageParams, PageDTO
from domain.account.entities import AccountEntity
from domain.abstract.entity import BaseEntity
from interfaces.fast_api.deps.account import get_current_account_or_none


class BaseCRUDApiViewSet[S: EntityCRUDService, E: BaseEntity, BIDTO: BaseItemDTO, BILDTO: BaseItemsListDTO,
                         BCIDTO: BaseCreateItemDTO, BUIDTO: BaseUpdateItemDTO]:
    """
    Generic CRUD API view set with support for service injection, DTOs and pagination.
    """
    service_type: Type[S]
    list_schema: Optional[Type[BILDTO]] = None
    schema: Optional[Type[BIDTO]] = None
    create_schema: Optional[Type[BCIDTO]] = None
    update_schema: Optional[Type[BUIDTO]] = None
    create_denied: bool = False
    update_denied: bool = False
    list_denied: bool = False
    retrieve_denied: bool = False
    get_auth: bool = False
    post_auth: bool = True
    update_auth: bool = True
    have_to_add_account_id_to_create_data: bool = False
    page_size: Optional[int] = None
    tags: list[str | Enum] = []

    def __init__(self, router: APIRouter) -> None:
        self.router = router

    def set_routes(self) -> None:
        if self.page_size:
            self.router.add_api_route(
                "/",
                self.list_view_with_pagination,
                methods=["GET"],
                response_model=PageDTO,
                tags=self.tags,
            )
        elif self.list_schema:
            response_model = list[self.list_schema]  # type: ignore[name-defined]
            self.router.add_api_route(
                "/",
                self.list_view,
                methods=["GET"],
                response_model=response_model,
                tags=self.tags,
            )
        if self.schema:
            self.router.add_api_route(
                "/{id:int}/",
                self.retrieve_view,
                methods=["GET"],
                response_model=self.schema,
                tags=self.tags,
            )
            self.router.add_api_route(
                "/",
                self.create_view,
                methods=["POST"],
                response_model=self.schema,
                status_code=status.HTTP_201_CREATED,
                tags=self.tags,
            )
            self.router.add_api_route(
                "/{id:int}/",
                self.update_view,
                methods=["PUT"],
                response_model=self.schema,
                tags=self.tags,
            )
        self.router.add_api_route(
            "/{id:int}/",
            self.delete_view,
            methods=["DELETE"],
            status_code=status.HTTP_204_NO_CONTENT,
            tags=self.tags,
        )

    def get_service(self) -> S:
        return self.service_type()

    async def _get_list(self, account: Optional[AccountEntity]) -> list[E]:
        service = self.get_service()
        return await service.list()

    async def list_view_with_pagination(
            self,
            account: Optional[AccountEntity] = Depends(get_current_account_or_none),
            params: PageParams = Depends(),
    ) -> PageDTO:
        if not self.list_schema:
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
        if self.get_auth and not account:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        if self.list_denied:
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
        entities = await self._get_list(account)
        return await paginate(entities, self.list_schema or self.schema, params)

    async def list_view(
            self,
            account: Optional[AccountEntity] = Depends(get_current_account_or_none),
    ) -> list[BILDTO]:
        if not self.list_schema:
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
        if self.get_auth and not account:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        await self._check_denied(self.list_denied, account)
        entities = await self._get_list(account)
        return [self.list_schema.model_validate(e.to_dict()) for e in entities]

    async def _get_retrieve(self, id: int, account: Optional[AccountEntity]) -> Optional[E]:
        service = self.get_service()
        return await service.get_by_id(id)

    async def retrieve_view(
            self,
            id: int,
            account: Optional[AccountEntity] = Depends(get_current_account_or_none),
    ) -> BIDTO:
        if not self.schema:
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
        if self.get_auth and not account:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        await self._check_denied(self.retrieve_denied, account)
        entity = await self._get_retrieve(id, account)
        if not entity:
            raise HTTPException(status_code=404, detail="Not found")
        return self.schema.model_validate(entity.to_dict())

    @staticmethod
    async def _check_denied(is_denied: bool, account: Optional[AccountEntity]) -> None:
        if not is_denied:
            return
        if account:
            await Accessor.set_repo()
            if await Accessor.is_superuser(account):
                return
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    async def create_view(
            self,
            request: Request,
            account: Optional[AccountEntity] = Depends(get_current_account_or_none),
    ) -> BIDTO:
        if self.post_auth and not account:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        if not self.create_schema or not self.schema:
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
        await self._check_denied(self.create_denied, account)
        j = await request.json()
        data = self.create_schema.model_validate(j)
        if self.have_to_add_account_id_to_create_data and account:
            data.account_id = account.id
        service = self.get_service()
        entity = service.from_create_dto(data)
        entity = await service.create(entity)
        return self.schema.model_validate(entity.to_dict())

    async def update_view(
            self,
            id: int,
            request: Request,
            account: Optional[AccountEntity] = Depends(get_current_account_or_none),
    ) -> BIDTO:
        if not self.update_schema or not self.schema:
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
        if self.update_auth and not account:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        await self._check_denied(self.update_denied, account)
        j = await request.json()
        data = self.update_schema.model_validate(j)
        service = self.get_service()
        old_entity = await service.get_by_id(id)
        updated_entity = service.from_update_dto(old_entity, data)
        saved_entity = await service.update(updated_entity, account)
        return self.schema.model_validate(saved_entity.to_dict())

    async def delete_view(
            self,
            id: int,
            account: Optional[AccountEntity] = Depends(get_current_account_or_none),
    ) -> Response:
        if self.update_auth and not account:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        await self._check_denied(self.update_denied, account)
        service = self.get_service()
        entity = await service.get_by_id(id)
        await service.delete(entity, account)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
