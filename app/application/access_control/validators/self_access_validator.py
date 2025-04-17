from domain.access_role.interfaces.validator import BaseAccessValidator
from domain.account.entities import AccountEntity
from domain.abstract import E


class SelfAccessValidator(BaseAccessValidator):
    async def has_access(self, entity: E, account: AccountEntity) -> bool:
        return entity.id == account.id
