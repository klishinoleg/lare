from typing import TYPE_CHECKING
from tortoise import fields
from infrastructure.repository.tortoise.models.abstract import AbstractModel

if TYPE_CHECKING:
    from .word import WordModel
    from .language import LanguageModel
    from .account import AccountModel


class WordTranslateModel(AbstractModel):
    """
    Stores translation metadata for a word.
    """

    if TYPE_CHECKING:
        word_id: int
        language_id: int
        account_id: int

    id = fields.IntField(primary_key=True)
    word: fields.ForeignKeyRelation["WordModel"] = fields.ForeignKeyField(
        "models.WordModel",
        related_name="translations",
        on_delete=fields.CASCADE,
    )
    language: fields.ForeignKeyRelation["LanguageModel"] = fields.ForeignKeyField(
        "models.LanguageModel",
        related_name="word_translations",
        on_delete=fields.CASCADE,
    )
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel",
        related_name="word_translations",
        on_delete=fields.CASCADE,
    )
    translate = fields.CharField(max_length=512)
    transliteration = fields.CharField(max_length=255, null=True)
    word_type = fields.CharField(max_length=64, null=True)
    gender = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "word_translate"
        unique_together = (("word_id", "language_id", "account_id"),)
