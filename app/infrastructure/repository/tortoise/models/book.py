from __future__ import annotations

from tortoise import fields
from tortoise_imagefield import ImageField
from typing import TYPE_CHECKING

from .abstract import AbstractModel
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .language import LanguageModel
    from .account import AccountModel


class BookModel(AbstractModel, TimestampMixin):
    """
    ORM model representing a book entry in the database.
    """
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    language: fields.ForeignKeyRelation["LanguageModel"] = fields.ForeignKeyField(
        "models.LanguageModel",
        related_name="books",
        on_delete=fields.CASCADE,
    )
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel",
        related_name="books",
        on_delete=fields.CASCADE,
    )
    chapters_count = fields.IntField(default=0)
    image = ImageField(field_for_name="name", directory_name="books_images")

    @property
    async def croped_image(self) -> str:
        return await getattr(self, "get_image_webp")(100, 250)

    class Meta:
        table = "books"
