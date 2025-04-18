from abc import ABC, abstractmethod
from domain.abstract import BaseEntity
from domain.account.entities import AccountEntity


class BaseAccessValidator[E: BaseEntity](ABC):
    """
    Interface for checking whether a user has access to a given entity.

    This validator must be implemented per entity type and registered in Authorizer.

    Method:
        has_access(entity: BaseEntity, account: AccountEntity) -> bool
    """

    @abstractmethod
    async def has_access(self, entity: E, account: AccountEntity) -> bool:
        """
        Determine whether the given account has permission to access the entity.

        Args:
            entity (BaseEntity): The domain entity to check access for.
            account (AccountEntity): The user attempting to access the entity.

        Returns:
            bool: True if the user has access, False otherwise.
        """
        ...
