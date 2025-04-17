from tortoise import fields
from .abstract import AbstractModel


class SegmentModel(AbstractModel):
    """
    ORM model representing a language-specific segment.
    """
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    language = fields.ForeignKeyField("models.LanguageModel", related_name="segments", on_delete=fields.CASCADE)

    class Meta:
        table = "segment"
        unique_together = (("language", "name"),)
