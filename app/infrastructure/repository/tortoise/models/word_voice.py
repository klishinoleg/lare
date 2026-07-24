from typing import TYPE_CHECKING
from tortoise import fields
from infrastructure.repository.tortoise.models.abstract import AbstractModel

if TYPE_CHECKING:
    from .word import WordModel


class WordVoiceModel(AbstractModel):
    """
    Links a word to a voice audio file path.
    """

    if TYPE_CHECKING:
        word_id: int

    id = fields.IntField(primary_key=True)
    word: fields.ForeignKeyRelation["WordModel"] = fields.ForeignKeyField(
        "models.WordModel",
        related_name="voices",
        on_delete=fields.CASCADE,
    )
    file_path = fields.CharField(max_length=255)

    class Meta:
        table = "word_voice"
        unique_together = (("word_id",),)
