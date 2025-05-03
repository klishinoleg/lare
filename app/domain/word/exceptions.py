from domain.abstract import EntityException, EntityNotFoundException, DomainValidationException


class WordException(EntityException):
    """Base exception for word-related domain errors."""
    ...


class WordNotFoundError(EntityNotFoundException):
    """Raised when a word is not found."""
    ...


class WordAlreadyExistsError(WordException, DomainValidationException):
    """Raised when a word with similar language id already exists."""
