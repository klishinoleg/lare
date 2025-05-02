from dataclasses import dataclass


@dataclass(slots=True)
class ChapterContentWordType:
    base: str
    origin: str
    lines: int = 0
