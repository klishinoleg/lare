from typing import TYPE_CHECKING
from tortoise import fields
from infrastructure.repository.tortoise.models.abstract import AbstractModel

if TYPE_CHECKING:
    from .segment import SegmentModel
    from .word_translate import WordTranslateModel


class WordTranslateSegmentTranslateModel(AbstractModel):
    """
    Links word translations to segment translations.
    """

    if TYPE_CHECKING:
        segment_translate_id: int
        word_translate_id: int

    id = fields.IntField(primary_key=True)
    segment_translate: fields.ForeignKeyRelation["SegmentModel"] = fields.ForeignKeyField(
        "models.SegmentTranslateModel",
        related_name="word_links",
        on_delete=fields.CASCADE
    )
    word_translate: fields.ForeignKeyRelation["WordTranslateModel"] = fields.ForeignKeyField(
        "models.WordTranslateModel",
        related_name="segment_links",
        on_delete=fields.CASCADE
    )

    class Meta:
        table = "word_translate_segment_translate"
        unique_together = (("segment_translate_id", "word_translate_id"),)
