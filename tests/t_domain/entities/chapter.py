import random

import factory
from domain.book.entities import ChapterEntity
from application.book.dtos.chapter import CreateChapterWithTextDTO
from faker import Faker

faker = Faker()


class ChapterFactory(factory.Factory):
    class Meta:
        model = ChapterEntity

    id = None
    name = factory.Faker("name")
    book_id = 1
    account_id = 1


class ChapterWithTextFactory(factory.Factory):
    class Meta:
        model = CreateChapterWithTextDTO

    name = factory.LazyFunction(lambda: f"Chapter {random.randint(1, 100)}: {faker.word().capitalize()}")
    book_id = factory.LazyFunction(lambda: random.randint(1, 10))
    source_url = factory.LazyFunction(lambda: faker.url())

    @factory.lazy_attribute
    def text(self) -> str:
        paragraphs = [faker.paragraph(nb_sentences=random.randint(3, 7)) for _ in range(random.randint(2, 5))]
        return "\n\n".join(paragraphs)
