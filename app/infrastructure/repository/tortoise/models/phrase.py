from tortoise import fields
from .abstract import AbstractModel


class PhraseModel(AbstractModel):
    """
    ORM model representing a language-specific word.
    """
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    language = fields.ForeignKeyField("models.LanguageModel", related_name="phrases", on_delete=fields.CASCADE)

    class Meta:
        table = "phrase"
        unique_together = (("language", "name"),)
