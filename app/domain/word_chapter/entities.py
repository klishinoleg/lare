from __future__ import annotations

from dataclasses import dataclass, field
from domain.abstract import BaseEntity


@dataclass(slots=True, kw_only=True)
class WordChapter(BaseEntity):
    """
    Index entity representing a word in a specific chapter, including its position and form.

    Attributes:
        word_id (int): Reference to the canonical WordEntity.
        chapter_id (int): Reference to the ChapterEntity.
        position (int): Position of the word in the chapter's flat text.
        name (str): Actual form of the word as it appeared in text (with symbols).
        n (int): Normalization level or token group indicator.
        phrase_id (int | None): Optional link to the phrase this word is part of.
        segment_id (int | None): Optional link to segment or sentence this word is part of.
    """
    name: str
    word_id: int
    chapter_id: int
    position: int
    n: int = field(default=0, repr=False)
    phrase_id: int | None = field(default=None, repr=False)
    segment_id: int | None = field(default=None, repr=False)
