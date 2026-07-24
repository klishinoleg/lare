from __future__ import annotations
from abc import abstractmethod
from domain.abstract import EntityRepository
from domain.ai.entities import AiModelEntity, AiLogEntity
from domain.finance.enums.account_usage_type import AccountUsageType


class AiModelRepository(EntityRepository[AiModelEntity]):
    """
    Repository interface for managing available AI models.
    """

    @abstractmethod
    async def get_by_model(self, model: str) -> AiModelEntity | None:
        """
        Retrieve an AI model by its internal identifier.
        """
        ...

    @abstractmethod
    async def get_available_for_usage(self, usage_type: AccountUsageType) -> list[AiModelEntity]:
        """
        Return all AI models that are allowed for a specific usage type.
        """
        ...


class AiLogRepository(EntityRepository[AiLogEntity]):
    """
    Repository interface for logging AI interactions and retrieving prior requests.
    """

    @abstractmethod
    async def get_by_hash(
            self,
            hash_str: str,
            usage_type: AccountUsageType,
            ai_type: str
    ) -> AiLogEntity | None:
        """
        Retrieve a request log by unique hash, usage type, and AI type.
        """
        ...
