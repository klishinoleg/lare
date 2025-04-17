from __future__ import annotations
from abc import ABC
from domain.abstract import EntityRepository
from domain.language.entities import LanguageEntity


class LanguageRepository(EntityRepository[LanguageEntity], ABC):
    """
    Abstract repository interface for Language entities.
    """
    ...
