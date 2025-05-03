from domain.abstract import EntityException, EntityNotFoundException, PermissionDenied


class BookException(EntityException):
    """Base exception for all Book-related domain errors."""
    ...


class BookNotFoundError(EntityNotFoundException):
    """Raised when a book is not found."""
    ...


class ChapterException(EntityException):
    """Base exception for Chapter-related domain errors."""
    ...


class ChapterNotFoundError(EntityNotFoundException):
    """Raised when a chapter is not found."""
    ...


class BookPermissionDenied(BookException, PermissionDenied):
    """Raised when the account does not have the required permissions for edit the book."""


class ChapterPermissionDenied(ChapterException, PermissionDenied):
    """Raised when the account does not have the required permissions for edit the chapter."""
