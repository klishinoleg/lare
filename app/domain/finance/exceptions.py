from domain.abstract import EntityException, EntityNotFoundException, PermissionDenied


# ---------- Base Exceptions ----------

class FinanceException(EntityException):
    """Base exception for all finance-related domain errors."""
    ...


# ---------- Transaction ----------

class AccountTransactionException(FinanceException):
    """Base exception for account transactions."""
    ...


class AccountTransactionNotFound(AccountTransactionException, EntityNotFoundException):
    """Raised when an account transaction is not found."""
    ...


class AccountTransactionStartBonusExist(AccountTransactionException):
    """Raised when an account has a start bonus."""
    ...


class AccountTransactionPermissionDenied(AccountTransactionException, PermissionDenied):
    """Permission denied for modifying an account transaction."""
    ...


# ---------- Usage ----------

class AccountUsageException(FinanceException):
    """Base exception for account usage."""
    ...


class AccountUsageNotFound(AccountUsageException, EntityNotFoundException):
    """Raised when an account usage record is not found."""
    ...


class AccountUsagePermissionDenied(AccountUsageException, PermissionDenied):
    """Permission denied for modifying account usage."""
    ...


# ---------- Bill ----------

class BillException(FinanceException):
    """Base exception for billing."""
    ...


class BillNotFound(BillException, EntityNotFoundException):
    """Raised when a bill is not found."""
    ...


class PaymentCreationError(BillException, EntityNotFoundException):
    """Raised when can't make payment for billing."""
    ...


class BillPermissionDenied(BillException, PermissionDenied):
    """Permission denied for modifying a bill."""
    ...


class BillRetrySuccessError(BillException):
    """When the bill already successfully."""
    ...


class BillRetryRefundError(BillException):
    """When the bill already refunded."""
    ...
