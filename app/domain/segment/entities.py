from dataclasses import dataclass
from domain.abstract import BaseEntity


@dataclass(slots=True, kw_only=True)
class SegmentEntity(BaseEntity):
    """
    Represents a distinct text segment (sentence, paragraph, etc.) for translation or dialogue.
    """
    name: str
    language_id: int
