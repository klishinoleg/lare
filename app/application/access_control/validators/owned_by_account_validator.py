from domain.access_role.interfaces.validator import BaseAccessValidator
from domain.account.entities import AccountEntity
from domain.abstract import E


class OwnedByAccountValidator(BaseAccessValidator):
    async def has_access(self, entity: E, account: AccountEntity) -> bool:
        return hasattr(entity, "account_id") and getattr(entity, "account_id") == account.id
