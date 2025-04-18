from collections import Counter
from application.book.datatypes.chapter_content import ChapterContentType
from application.book.services.word_processing import split_text_into_words


async def process_text_to_chapters(text: str) -> list[ChapterContentType]:
    """
    Asynchronously process text and split it into logical chapters.

    Args:
        text (str): Raw chapter text.

    Returns:
        List[ChapterContentWordType]: List of parsed chapters with chapter name and list of words.
    """
    lines = text.splitlines()
    empty_line_counts = []
    consecutive_empty_lines = 0

    for line in lines:
        if line.strip():
            if consecutive_empty_lines > 0:
                empty_line_counts.append(consecutive_empty_lines)
            consecutive_empty_lines = 0
        else:
            consecutive_empty_lines += 1

    most_common_empty_lines = (
        Counter(empty_line_counts).most_common(1)[0][0] if empty_line_counts else 1
    )

    chapters: list[ChapterContentType] = []
    current_chapter = ChapterContentType()
    chapter_text: list[str] = []
    empty_line_count = 0

    for line in lines:
        if line.strip():
            if empty_line_count > most_common_empty_lines:
                current_chapter.name = await extract_chapter_name(chapter_text)
                current_chapter.words = split_text_into_words(chapter_text)
                chapters.append(current_chapter)
                current_chapter = ChapterContentType()
                chapter_text = []
            chapter_text.append(line)
            empty_line_count = 0
        else:
            empty_line_count += 1

    if chapter_text:
        chapter_name = await extract_chapter_name(chapter_text)
        current_chapter.name = chapter_name
        current_chapter.words = split_text_into_words(chapter_text)
        chapters.append(current_chapter)
    return chapters


async def extract_chapter_name(chapter_text: list[str]) -> str:
    """
    Extract the chapter title based on heuristics.

    Args:
        chapter_text (List[str]): Lines of the chapter.

    Returns:
        str: Chapter title.
    """
    if not chapter_text:
        return ""

    for line in chapter_text:
        if len(line.strip()) <= 100:
            return line.strip()

    return chapter_text[0][:50].strip() if chapter_text else ""
