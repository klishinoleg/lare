from tortoise import fields
from .abstract import AbstractModel


class WordModel(AbstractModel):
    """
    ORM model representing a language-specific word.
    """
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    language = fields.ForeignKeyField("models.LanguageModel", related_name="words", on_delete=fields.CASCADE)

    class Meta:
        table = "word"
        unique_together = (("language", "name"),)
