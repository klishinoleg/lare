from domain.access_role.interfaces.validator import BaseAccessValidator
from domain.account.entities import AccountEntity
from domain.abstract import BaseEntity


class SelfAccessValidator[E: BaseEntity](BaseAccessValidator[E]):
    async def has_access(self, entity: E, account: AccountEntity) -> bool:
        return entity.id == account.id
