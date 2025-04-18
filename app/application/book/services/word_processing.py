import re
import regex

from application.book.datatypes.chapter_content import ChapterContentWordType


def split_text_into_words(chapter_text: list[str]) -> list[ChapterContentWordType]:
    """
    Split text lines into a list of words with punctuation and spacing handling.

    Args:
        chapter_text (List[str]): Raw lines from the chapter.

    Returns:
        List[ChapterContentWordType]: List of words with prefixes, postfixes and line breaks count.
    """
    words: list[ChapterContentWordType] = []
    empty_line_count = 0

    def add_lines_count(w: list[ChapterContentWordType], elc: int) -> None:
        if w:
            w[-1].lines = elc

    current_prefix = None
    for line in chapter_text:
        is_start_line = True
        if line.strip():
            empty_line_count = 1
            line_words = (
                re.sub(r'\s', ' ', line.replace("\u00A0", " ").replace("--", " "))
                .strip()
                .split(" ")
            )
            for word in line_words:
                prefix = ""
                postfix = ""
                skip = False
                if not word.isalnum():
                    match = regex.match(
                        r"^([^\p{L}\d]*)([\p{L}\d]+[\p{L}\d\'\’\-]*[\p{L}\d]+)([^\p{L}\d]*)$", word
                    )
                    if match and match.group(2) != '-':
                        prefix = match.group(1)
                        word = match.group(2).replace("'", '’').replace("--", "-").replace("–", "-")
                        postfix = match.group(3)
                    elif len(word) < 3:
                        skip = True
                        if words and not is_start_line:
                            words[-1].origin += f" {word}"
                        else:
                            current_prefix = word

                if not skip:
                    if current_prefix:
                        prefix = current_prefix + ' ' + prefix
                        current_prefix = None
                    words.append(ChapterContentWordType(base=word, origin=f"{prefix}{word}{postfix}".strip()))

                is_start_line = False
            add_lines_count(words, empty_line_count + 1)
        else:
            empty_line_count += 1
            add_lines_count(words, empty_line_count)

    return words
