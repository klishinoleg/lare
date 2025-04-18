from dataclasses import dataclass
from domain.abstract import BaseEntity


@dataclass(slots=True, kw_only=True)
class PhraseEntity(BaseEntity):
    """
    Represents a phrase (multi-word expression) extracted from text and optionally translated or voiced.
    """
    name: str
    language_id: int
