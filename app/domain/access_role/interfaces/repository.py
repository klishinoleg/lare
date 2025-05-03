from abc import ABC, abstractmethod
from domain.abstract import EntityRepository
from domain.access_role.entities import AccessRoleEntity
from domain.access_role.enums.roles import AccessRole


class AccessRoleRepository(EntityRepository[AccessRoleEntity], ABC):
    @abstractmethod
    async def get_account_role(self, account_id: int) -> AccessRole:
        """
        Returns the role enum of the account.
        If not found — return the highest number (lowest priority).
        """
        ...

    async def has_role(self, account_id: int, target: AccessRole) -> bool:
        role = await self.get_account_role(account_id)
        return role <= target
