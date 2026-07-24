from domain.abstract import EntityException, DomainValidationException, PermissionDenied, EntityNotFoundException


class AiException(EntityException):
    """Base exception for all AI-related errors."""
    ...


class AiModelNotFoundError(AiException):
    """Raised when the specified AI model is not found in the registry."""
    ...


class AiLogNotFoundError(EntityNotFoundException):
    """Raised when the specified AI log is not found in the registry."""
    ...


class AiLogPermissionDenied(PermissionDenied):
    """Raised when the specified AI log is denied."""
    ...


class AiModelAccessDenied(AiException, DomainValidationException):
    """Raised when an AI model is not allowed for the specified usage type."""
    ...


class AiRequestDuplicateError(AiException):
    """Raised when a request with the same hash has already been processed."""
    ...


class AiModelPermissionDenied(AiException, PermissionDenied):
    """Raised when an AI model is not allowed for the specified usage type."""


class AiResponseInvalidError(AiException, DomainValidationException):
    """Raised when the response from the AI provider is invalid or missing expected fields."""
    ...


class AiProviderInternalError(AiException):
    """Raised when a provider (Google, GPT, etc.) fails or returns an unexpected error."""
    ...
