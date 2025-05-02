from dataclasses import dataclass, field
from domain.abstract import BaseEntity


@dataclass(slots=True, kw_only=True)
class LanguageEntity(BaseEntity):
    """
    Represents a supported language.
    """
    name: str
    slug: str
    original_name: str = field(repr=False)
    code: str
    ordering: int = field(default=100, repr=False)
