from domain.access_role.entities import AccessRoleEntity
from domain.access_role.enums.roles import AccessRole
from domain.access_role.interfaces.repository import AccessRoleRepository
from infrastructure.repository.mock.base_repository import BaseMockRepository


class MockAccessRoleRepository(BaseMockRepository[AccessRoleEntity], AccessRoleRepository):
    async def get_account_role(self, account_id: int) -> AccessRole:
        role = next((r for r in self.entities.values() if r.account_id == account_id), None)
        if not role:
            return AccessRole.NOT_ROLE
        return role.role

    async def has_role(self, account_id: int, target: AccessRole) -> bool:
        return await super().has_role(account_id, target)
