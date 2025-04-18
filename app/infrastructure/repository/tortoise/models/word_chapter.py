from __future__ import annotations

from tortoise import fields
from typing import TYPE_CHECKING

from .abstract import AbstractModel

if TYPE_CHECKING:
    from .word import WordModel
    from .chapter import ChapterModel
    from .phrase import PhraseModel
    from .segment import SegmentModel


class WordChapterModel(AbstractModel):
    """
    ORM model linking a word to a specific chapter and position.
    """

    if TYPE_CHECKING:
        word_id: int
        chapter_id: int
        phrase_id: int | None
        segment_id: int | None

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    word: fields.ForeignKeyRelation["WordModel"] = fields.ForeignKeyField(
        "models.WordModel",
        related_name="words_uses",
        on_delete=fields.CASCADE,
    )
    chapter: fields.ForeignKeyRelation["ChapterModel"] = fields.ForeignKeyField(
        "models.ChapterModel",
        related_name="chapter_words",
        on_delete=fields.CASCADE,
    )
    position = fields.IntField()
    n = fields.IntField(default=0)
    phrase: fields.ForeignKeyRelation["PhraseModel"] | None = fields.ForeignKeyField(
        "models.PhraseModel",
        related_name="phrase_words",
        on_delete=fields.SET_NULL,
        null=True,
    )
    segment: fields.ForeignKeyRelation["SegmentModel"] | None = fields.ForeignKeyField(
        "models.SegmentModel",
        related_name="segment_words",
        on_delete=fields.SET_NULL,
        null=True,
    )

    class Meta:
        table = "word_chapter"
