from application.access_control.services import Accessor
from domain.access_role.enums.roles import AccessRole
from domain.access_role.interfaces.validator import BaseAccessValidator
from domain.account.entities import AccountEntity
from domain.abstract import BaseEntity


class AdministratorValidator[E: BaseEntity](BaseAccessValidator[E]):
    async def has_access(self, entity: E, account: AccountEntity) -> bool:
        return await Accessor.has_role(account, AccessRole.ADMINISTRATOR)
