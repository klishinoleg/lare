from typing import Callable

from domain.access_role.interfaces.validator import BaseAccessValidator
from domain.account.entities import AccountEntity
from domain.book.entities import ChapterEntity
from application.access_control.services import Accessor


class ChapterAccessValidator(BaseAccessValidator[ChapterEntity]):
    def __init__(self, book_loader: Callable) -> None:
        self.book_loader: Callable = book_loader

    async def has_access(self, entity: ChapterEntity, account: AccountEntity) -> bool:
        book = await self.book_loader(entity)
        await Accessor.or_raise(book, account)
        return True
