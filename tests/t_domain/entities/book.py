import factory
from domain.book.entities import BookEntity


class BookFactory(factory.Factory):
    class Meta:
        model = BookEntity

    id = None
    name = factory.Faker("name")
    image = "https://fastly.picsum.photos/id/443/200/300.jpg?hmac=lXwP6DouUwgwHCQ9ZcgkX6W237U8PAyS9o-YAD1zvN8"
    language_id = 1
    account_id = 1
