from application.book.services.book_crud_service import BookService
from domain.access_role.interfaces.validator import BaseAccessValidator
from domain.account.entities import AccountEntity
from domain.book.entities import ChapterEntity
from application.access_control.services import Accessor


class ChapterAccessValidator(BaseAccessValidator[ChapterEntity]):
    async def has_access(self, entity: ChapterEntity, account: AccountEntity) -> bool:
        book = await BookService().get_by_id(entity.book_id)
        await Accessor.or_raise(book, account)
        return True
