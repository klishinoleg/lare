from domain.abstract.exceptions import EntityException, EntityNotFoundException, PermissionDenied


class LanguageException(EntityException):
    """
    Base exception for language domain-related errors.
    """
    ...


class LanguageNotFoundError(EntityNotFoundException, LanguageException):
    """
    Raised when a language with the specified ID or code is not found.
    """
    ...


class LanguagePermissionDenied(PermissionDenied, LanguageException):
    """
    Raised when a language update denied
    """
