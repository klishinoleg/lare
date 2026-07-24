from __future__ import annotations

from tortoise import fields
from typing import TYPE_CHECKING

from .abstract import AbstractModel

if TYPE_CHECKING:
    from .language import LanguageModel


class SegmentModel(AbstractModel):
    """
    ORM model representing a language-specific segment.
    """

    if TYPE_CHECKING:
        language_id: int

    id = fields.IntField(primary_key=True)
    name = fields.TextField()
    language: fields.ForeignKeyRelation["LanguageModel"] = fields.ForeignKeyField(
        "models.LanguageModel",
        related_name="segments",
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = "segment"
        unique_together = (("language", "name"),)
