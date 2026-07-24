from domain.text_data.exceptions import TextDataException


class WordTranslateNotFoundError(TextDataException):
    """Raised when a word translation is not found."""


class WordVoiceNotFoundError(TextDataException):
    """Raised when a word voice record is missing."""
