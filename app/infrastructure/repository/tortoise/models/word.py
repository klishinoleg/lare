from __future__ import annotations

from tortoise import fields
from typing import TYPE_CHECKING

from .abstract import AbstractModel

if TYPE_CHECKING:
    from .language import LanguageModel


class WordModel(AbstractModel):
    """
    ORM model representing a language-specific word.
    """

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    language: fields.ForeignKeyRelation["LanguageModel"] = fields.ForeignKeyField(
        "models.LanguageModel",
        related_name="words",
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = "word"
        unique_together = (("language", "name"),)
