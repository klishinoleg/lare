from dataclasses import dataclass

from domain.abstract import BaseEntity


@dataclass(slots=True, kw_only=True)
class WordTranslateEntity(BaseEntity):
    """
    Stores translation metadata for a single word.

    Attributes:
        word_id (int): ID of the word.
        language_id (int): Target language.
        account_id (int): Who requested translation.
        translate (str): Translated word.
        transliteration (str | None): Optional pronunciation guide.
        word_type (str | None): Grammatical or lexical type (e.g., noun).
        gender (str | None): Gender of the word, if applicable.
    """
    word_id: int
    language_id: int
    account_id: int
    translate: str
    transliteration: str | None = None
    word_type: str | None = None
    gender: str | None = None


@dataclass(slots=True, kw_only=True)
class WordVoiceEntity(BaseEntity):
    """
    Links a word to a voice audio file path.

    Attributes:
        word_id (int): The word that was voiced.
        file_path (str): Path to the audio file.
    """
    word_id: int
    file_path: str
