import factory
from domain.book.entities import ChapterEntity


class ChapterFactory(factory.Factory):
    class Meta:
        model = ChapterEntity

    id = None
    name = factory.Faker("name")
    book_id = 1
    account_id = 1
