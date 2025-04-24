from __future__ import annotations

from tortoise import fields
from typing import TYPE_CHECKING

from .abstract import AbstractModel

if TYPE_CHECKING:
    from .book import BookModel
    from .account import AccountModel


class ChapterModel(AbstractModel):
    """
    ORM model representing a chapter entry in the database.
    """
    if TYPE_CHECKING:
        book_id: int
        account_id: int

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    book: fields.ForeignKeyRelation["BookModel"] = fields.ForeignKeyField(
        "models.BookModel",
        related_name="chapters",
        on_delete=fields.CASCADE,
    )
    account: fields.ForeignKeyRelation["AccountModel"] = fields.ForeignKeyField(
        "models.AccountModel",
        related_name="chapters",
        on_delete=fields.CASCADE
    )
    source_url = fields.CharField(max_length=500)
    position = fields.IntField(default=0)
    is_ready = fields.BooleanField(default=False)

    class Meta:
        table = "chapter"
