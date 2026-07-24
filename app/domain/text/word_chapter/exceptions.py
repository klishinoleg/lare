from domain.abstract import EntityException, DomainValidationException, EntityNotFoundException


class WordChapterException(EntityException):
    """Base exception for chapter-word indexing errors."""
    ...


class WordChapterAlreadyExists(WordChapterException, DomainValidationException):
    """Raised when a chapter-word already exists with same word, chapter and position"""
    ...


class WordChapterEntityNotFound(EntityNotFoundException):
    """Raised when a chapter-word is not found"""
