from dataclasses import dataclass
from domain.abstract import BaseEntity


@dataclass(slots=True, kw_only=True)
class SegmentTranslateEntity(BaseEntity):
    """
    Stores AI-generated translation result for a segment.

    Attributes:
        segment_id (int): The segment this translation is linked to.
        account_id (int): The account that requested the translation.
        language_id (int): Target language for translation.
        translate (str): Resulting translated text.
    """
    segment_id: int
    account_id: int
    language_id: int
    translate: str


@dataclass(slots=True, kw_only=True)
class SegmentVoiceEntity(BaseEntity):
    """
    Links a segment to a voice audio file path.

    Attributes:
        segment_id (int): The segment that was voiced.
        file_path (str): Path to the generated voice file.
    """
    segment_id: int
    file_path: str


@dataclass(slots=True, kw_only=True)
class WordTranslateSegmentTranslateEntity(BaseEntity):
    """
    Index linking translated words to the segment translation.

    Attributes:
        segment_id (int): Segment translation reference.
        word_translate_id (int): Word translation reference.
    """
    segment_id: int
    word_translate_id: int

