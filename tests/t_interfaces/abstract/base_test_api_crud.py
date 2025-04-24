from __future__ import annotations

import pytest
from application.auth.dtos import AuthResponseDTO
from .base_client import BaseClientTest
from typing import Optional, Type
from httpx import Response
from time import sleep
from domain.abstract import BaseEntity
from application.abstract.dtos import BaseItemDTO, BaseItemsListDTO, BaseCreateItemDTO, BaseUpdateItemDTO
from factory import Factory
from httpx import AsyncClient


class BaseAPICRUDTest[E: BaseEntity, F: Factory, BIDTO:BaseItemDTO, BILDTO: BaseItemsListDTO, BCIDTO: BaseCreateItemDTO,
                      BUIDTO: BaseUpdateItemDTO](BaseClientTest):
    route: str  # example: "/account"
    # Factory method to generate test entities
    factory: Type[F]
    init_create_dto: Type[BCIDTO]
    init_update_dto: Type[BUIDTO]
    init_list_dto: Type[BILDTO]
    init_item_dto: Type[BIDTO]
    _created_at_field = 'created_at'
    _updated_at_field = "updated_at"

    @staticmethod
    def _get_auth_headers(auth_user_data: AuthResponseDTO) -> dict:
        return {"Authorization": f"Bearer {auth_user_data.token}"}

    async def _post(self, client: AsyncClient, data: BCIDTO, headers: dict | None = None) -> Response:
        return await client.post(self.route + "/", json=data.model_dump(), headers=headers)

    async def _get(self, client: AsyncClient, id: Optional[int] = None, path: str = "",
                   headers: dict | None = None) -> Response:
        url = f"{self.route}/{id}/" if id else self.route
        if path:
            url += f"/{path}/"
        return await client.get(url, headers=headers)

    async def _put(self, client: AsyncClient, id: int, data: BUIDTO, headers: dict | None = None) -> Response:
        return await client.put(f"{self.route}/{id}/", json=data.model_dump(), headers=headers)

    async def _delete(self, client: AsyncClient, id: int, headers: dict | None = None) -> Response:
        return await client.delete(f"{self.route}/{id}/", headers=headers)

    async def _create_entity(self, client: AsyncClient, auth_user_data: AuthResponseDTO) -> tuple[E, Response]:
        entity = await self._from_factory(client, auth_user_data)
        create_dto = self.init_create_dto.create_from_dict(entity.to_dict(exclude_id=True))
        return entity, await self._post(client, create_dto, headers=self._get_auth_headers(auth_user_data))

    async def _from_factory(self, client: AsyncClient, auth_user_data: AuthResponseDTO, **kwargs: dict) -> E:
        return self.factory(**kwargs)  # type: ignore[return-value]

    async def test_create_multiple(self, client: AsyncClient, auth_user_data: AuthResponseDTO) -> None:
        ids = []
        for _ in range(10):
            entity, response = await self._create_entity(client, auth_user_data)
            assert response.status_code == 201
            ids.append(response.json()["id"])
        assert len(set(ids)) == 10

    @pytest.mark.asyncio
    async def test_update_entities(self, client: AsyncClient, auth_user_data: AuthResponseDTO) -> None:
        entity, response = await self._create_entity(client, auth_user_data)
        assert response.status_code == 201
        initial_data = response.json()
        entity_id = response.json()["id"]
        updated_entity = await self._from_factory(client, auth_user_data)
        update_dto = self.init_update_dto.create_from_dict(updated_entity.to_dict(exclude_id=True))
        if initial_data.get(self._updated_at_field):
            sleep(1)
        response = await self._put(client, entity_id, update_dto, headers=self._get_auth_headers(auth_user_data))
        assert response.status_code == 200
        data = response.json()
        if initial_data.get(self._updated_at_field):
            assert data.get(self._updated_at_field) != initial_data.get(self._updated_at_field)
            assert data.get(self._created_at_field) == initial_data.get(self._created_at_field)
        for k, v in update_dto.model_dump().items():
            if k == "image":
                continue
            assert data[k] == v

    @pytest.mark.asyncio
    async def test_delete_entity(self, client: AsyncClient, auth_user_data: AuthResponseDTO) -> None:
        entity, response = await self._create_entity(client, auth_user_data=auth_user_data)
        entity_id = response.json()["id"]

        delete_response = await self._delete(client, entity_id, headers=self._get_auth_headers(auth_user_data))
        assert delete_response.status_code == 204

        second_delete = await self._delete(client, entity_id, headers=self._get_auth_headers(auth_user_data))
        assert second_delete.status_code == 404

        get_response = await self._get(client, entity_id, headers=self._get_auth_headers(auth_user_data))
        assert get_response.status_code == 404
