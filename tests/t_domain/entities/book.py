import base64
import os
import factory
from domain.book.entities import BookEntity


class BookFactory(factory.Factory):
    class Meta:
        model = BookEntity

    id = None
    name = factory.Faker("name")
    language_id = 1
    account_id = 1

    @factory.lazy_attribute
    def image(self) -> str:
        """Load 'test.png' from the same folder and encode it as base64."""
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, "test.png")
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:image/png;base64,{encoded_string}"
