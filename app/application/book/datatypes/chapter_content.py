from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class ChapterContentWordType:
    base: str
    origin: str
    lines: int = 0


@dataclass(slots=True)
class ChapterContentType:
    name: str = ""
    words: List[ChapterContentWordType] = field(default_factory=list)
