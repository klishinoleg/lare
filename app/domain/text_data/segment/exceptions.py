from domain.abstract import DomainValidationException
from domain.text_data.exceptions import TextDataException


class SegmentTranslateNotFoundError(TextDataException):
    """Raised when a segment translation is not found."""


class SegmentVoiceNotFoundError(TextDataException):
    """Raised when a segment voice record is missing."""


class WordTranslateSegmentLinkError(TextDataException, DomainValidationException):
    """Raised when linking a word translate to a segment fails due to invalid data or constraints."""
