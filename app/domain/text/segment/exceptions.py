from domain.abstract import EntityException, DomainValidationException, PermissionDenied


class SegmentException(EntityException):
    """Base exception for segment-related errors."""


class SegmentNotFoundError(SegmentException):
    """Raised when a segment is not found."""


class SegmentPermissionDenied(SegmentException, PermissionDenied):
    """Raised when user tries to access a segment without permission."""


class SegmentAlreadyExistsError(SegmentException, DomainValidationException):
    """Raised when a segment with the same name and language already exists."""


class SegmentInvalidIndexesError(SegmentException, DomainValidationException):
    """Raised when provided word indexes are invalid or inconsistent."""
