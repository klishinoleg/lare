from typing import TYPE_CHECKING
from tortoise import fields
from infrastructure.repository.tortoise.models.abstract import AbstractModel

if TYPE_CHECKING:
    from .account import AccountModel
    from .segment import SegmentModel
    from .language import LanguageModel


class SegmentTranslateModel(AbstractModel):
    """
    Stores AI-generated translation result for a segment.
    """

    if TYPE_CHECKING:
        segment_id: int
        account_id: int
        language_id: int

    id = fields.IntField(primary_key=True)
    segment: fields.ForeignKeyRelation["SegmentModel"] = fields.ForeignKeyField(
        "models.SegmentModel",
        related_name="translations",
        on_delete=fields.CASCADE
    )

    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel",
        on_delete=fields.CASCADE,
        related_name="translations")
    language: fields.ForeignKeyRelation["LanguageModel"] = fields.ForeignKeyField(
        "models.LanguageModel",
        on_delete=fields.CASCADE,
        related_name="translations")
    translate = fields.TextField()

    class Meta:
        table = "segment_translate"
        unique_together = (("segment_id", "language_id", "account_id"),)
