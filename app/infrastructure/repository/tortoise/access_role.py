from __future__ import annotations
from infrastructure.repository.tortoise.base_repository import BaseTortoiseRepository
from domain.access_role.entities import AccessRoleEntity
from domain.access_role.enums.roles import AccessRole
from domain.access_role.interfaces.repository import AccessRoleRepository
from infrastructure.repository.tortoise.models.access_role import AccessRoleModel


class TortoiseAccessRoleRepository(BaseTortoiseRepository[AccessRoleEntity, AccessRoleModel], AccessRoleRepository):
    model = AccessRoleModel

    async def get_account_role(self, account_id: int) -> AccessRole:
        role_obj = await self.model.filter(account_id=account_id).first()
        return role_obj.role if role_obj else AccessRole.NOT_ROLE

    async def has_role(self, account_id: int, target: AccessRole) -> bool:
        return await super().has_role(account_id, target)

    @staticmethod
    async def to_entity(obj: AccessRoleModel | None) -> AccessRoleEntity | None:
        if obj is None:
            return None
        return AccessRoleEntity(id=obj.id, account_id=obj.account_id, role=obj.role)
