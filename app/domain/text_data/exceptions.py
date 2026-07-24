from domain.abstract import EntityException, DomainValidationException


class TextDataException(EntityException):
    """Base exception for all translation-related errors."""
    ...
