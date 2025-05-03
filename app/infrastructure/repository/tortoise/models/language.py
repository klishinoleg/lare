from tortoise import fields
from .abstract import AbstractModel


class LanguageModel(AbstractModel):
    """
    Tortoise ORM model for supported languages.
    """
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    slug = fields.CharField(max_length=50, unique=True)
    code = fields.CharField(max_length=10)
    original_name = fields.CharField(max_length=100)
    ordering = fields.IntField(default=100)

    class Meta:
        table = "languages"
        ordering = ("ordering", "id")
