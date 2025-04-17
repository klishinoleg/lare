from tortoise import fields
from .abstract import AbstractModel


class ChapterModel(AbstractModel):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    book = fields.ForeignKeyField("models.BookModel", related_name="chapters", on_delete=fields.CASCADE)
    source_url = fields.CharField(max_length=500)
    position = fields.IntField(default=0)
    is_ready = fields.BooleanField(default=False)

    class Meta:
        table = "chapter"
