from __future__ import annotations

from dataclasses import dataclass, field

from domain.abstract import BaseEntity
from domain.mixins.timestamp_mixin import TimestampMixin


@dataclass(slots=True, kw_only=True)
class BookEntity(BaseEntity, TimestampMixin):
    """
    Book entity: aggregate root that holds chapters and metadata.
    """
    name: str
    language_id: int
    account_id: int
    image: str | None = field(repr=False)
    chapters_cnt: int = field(default=0)


@dataclass(slots=True, kw_only=True)
class ChapterEntity(BaseEntity, TimestampMixin):
    """
    Chapter entity: belongs to a book and holds text processing metadata.
    """
    name: str
    book_id: int
    account_id: int
    source_url: str | None = field(default=False, repr=False)
    position: int = field(default=50, repr=False)
    is_ready: bool = field(default=False)
