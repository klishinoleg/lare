from domain.abstract import EntityException, EntityNotFoundException, DomainValidationException


class AuthProfileException(EntityException):
    """Base exception for all authorization profile related errors."""
    ...


class AuthProfileNotFoundError(EntityNotFoundException):
    """Raised when the authorization profile is not found in the database."""
    ...


class AuthProfileAlreadyExistsError(AuthProfileException, DomainValidationException):
    """Raised when an authorization profile already exists for the given provider and ID."""
    ...


class AuthProfileInvalidCredentialsError(AuthProfileException, DomainValidationException):
    """Raised when the provided authorization profile data is invalid or fails verification."""
    ...


class AuthPasswordRegistrationValidationError(AuthProfileException, DomainValidationException):
    """Raised when the provided authorization profile data is invalid or fails verification."""
    ...


class AuthProviderNotRegistered(DomainValidationException):
    """
    Raised when no provider implementation is registered for a given provider type.

    Typically used by the AuthProviderFactory when a requested AuthProviderType
    (e.g. TELEGRAM, WHATSAPP) has not been registered via `AuthProviderFactory.register()`.

    Example:
        raise AuthProviderNotRegistered(f"No auth provider registered for: {provider_type}")
    """
    ...
