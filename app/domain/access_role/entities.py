from dataclasses import dataclass
from domain.abstract import BaseEntity
from domain.access_role.enums.roles import AccessRole


@dataclass(slots=True, kw_only=True)
class AccessRoleEntity(BaseEntity):
    account_id: int
    role: AccessRole
