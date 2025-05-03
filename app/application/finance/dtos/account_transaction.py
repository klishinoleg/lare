from decimal import Decimal
from pydantic import Field
from domain.finance.enums.transaction_type import TransactionType
from application.abstract.dtos import BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemDTO, BaseItemsListDTO


class CreateAccountTransactionDTO(BaseCreateItemDTO):
    """
    DTO used to create a new account transaction.
    """
    account_id: int = Field(..., description="The ID of the account related to the transaction.")
    transaction_type: TransactionType = Field(..., description="The type of the transaction.")
    credits_amount: Decimal = Field(..., description="The credit value involved in the transaction.")
    usage_id: int | None = Field(None, description="Related usage ID if applicable.")
    bill_id: int | None = Field(None, description="Related bill ID if applicable.")


class UpdateAccountTransactionDTO(BaseUpdateItemDTO):
    """
    DTO used to update an existing account transaction.
    """
    transaction_type: TransactionType | None = Field(None, description="The new type of the transaction.")
    credits_amount: Decimal | None = Field(None, description="The updated credit amount.")
    usage_id: int | None = Field(None, description="Updated usage reference if applicable.")
    bill_id: int | None = Field(None, description="Updated bill reference if applicable.")


class AccountTransactionDTO(BaseItemDTO):
    """
    DTO representing a complete view of an account transaction.
    """
    id: int
    account_id: int = Field(..., description="The ID of the account related to the transaction.")
    transaction_type: TransactionType = Field(..., description="The type of the transaction.")
    credits_amount: Decimal = Field(..., description="The credit value involved in the transaction.")
    usage_id: int | None = Field(None, description="Related usage ID if applicable.")
    bill_id: int | None = Field(None, description="Related bill ID if applicable.")


class AccountTransactionListDTO(BaseItemsListDTO):
    """
    DTO representing a summary view of a transaction for list displays.
    """
    id: int
    transaction_type: TransactionType = Field(..., description="The type of the transaction.")
    credits_amount: Decimal = Field(..., description="The credit value involved in the transaction.")
