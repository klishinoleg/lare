from application.book.datatypes.chapter_content import ChapterContentWordType
from application.book.utils.word_processing import split_text_into_words


async def process_text_to_chapters(text: str) -> list[ChapterContentWordType]:
    """
    Asynchronously process text and split it into logical chapters.

    Args:
        text (str): Raw chapter text.

    Returns:
        List[ChapterContentWordType]: List of parsed chapters with chapter name and list of words.
    """
    lines = text.splitlines()
    return split_text_into_words(lines)
