from domain.abstract import EntityException, DomainValidationException


class ChapterWordException(EntityException):
    """Base exception for chapter-word indexing errors."""
    ...


class ChapterWordAlreadyExists(ChapterWordException, DomainValidationException):
    """Raised when a chapter-word already exists with same word, chapter and position"""
    ...
