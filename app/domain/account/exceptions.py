from domain.abstract import EntityException, EntityNotFoundException, DomainValidationException, PermissionDenied


class AccountException(EntityException):
    """
    Base exception for all account-related domain errors.

    Use this class as the parent for any exceptions that occur
    while working with Account entities.
    """
    ...


class AccountNotFoundError(EntityNotFoundException):
    """
    Raised when an account is not found in the database or repository.
    """
    ...


class AccountAlreadyExistsError(AccountException):
    """
    Raised when an attempt is made to create an account that already exists.
    Typically triggered by a uniqueness violation on email or username.
    """
    ...


class NotEnoughCreditsError(AccountException):
    """
    Raised when an account does not have sufficient credits to perform an operation.
    """
    ...


class NotUniqueUsernameError(AccountException, DomainValidationException):
    """
    Raised when a username is already taken during account creation or update.

    Inherits from DomainValidationException to allow use in validation chains.
    """
    ...


class AccountPermissionDenied(AccountException, PermissionDenied):
    """Raised when an account does not have sufficient permissions to perform an operation."""
