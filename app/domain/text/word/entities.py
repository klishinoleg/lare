from dataclasses import dataclass
from domain.abstract import BaseEntity


@dataclass(slots=True, kw_only=True)
class WordEntity(BaseEntity):
    """
    Domain entity representing a word in a specific language.

    Attributes:
        name (str): The normalized form of the word (e.g. uppercased).
        language_id (int): ID of the language this word belongs to.
    """
    name: str
    language_id: int
