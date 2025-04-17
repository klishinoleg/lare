from __future__ import annotations

from typing import TypeVar


class DomainException(Exception):
    """
    Base exception for all domain-level errors.

    This is a generic exception used to represent any error that occurs
    within the domain layer of the application. All other domain exceptions
    should inherit from this class.
    """
    ...


class DomainValidationException(Exception):
    """
    Raised when a domain-level validation rule is violated.

    This exception is typically used to indicate that input data or entity
    state does not satisfy required business rules.

    Attributes:
        message (str): Explanation of the validation failure.
        field (str): Optional name of the field or property that caused the failure.
    """

    def __init__(self, message: str = "Domain exception", *args, field: str = ""):
        self.message = message
        self.field = field
        super().__init__(self.message, *args)

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message


class EntityException(DomainException):
    """
    Base exception for errors related to domain entities.
    """
    ...


class DTOException(DomainException):
    """
    Base exception for errors related to data transfer objects (DTOs).
    """
    ...


class EntityNotFoundException(EntityException):
    """
    Raised when an entity could not be found in the repository or database.
    """
    ...


class NotDefinedRepositoryException(EntityException):
    """
    Raised when an entity is not defined in the repository.
    """


class PermissionDenied(Exception):
    """
    Raised when access to a domain entity is denied.

    This is the default exception thrown by the Authorizer
    when no specific exception is registered for the entity type.
    """
    ...


PDEXC = TypeVar("PDEXC", bound=PermissionDenied)
