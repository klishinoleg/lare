from decimal import Decimal
from pydantic import Field
from domain.finance.enums.account_usage_type import AccountUsageType
from application.abstract.dtos import BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemDTO, BaseItemsListDTO


class CreateAccountUsageDTO(BaseCreateItemDTO):
    """
    DTO used to create a new record of account usage.
    """
    account_id: int = Field(..., description="The ID of the account consuming the resource.")
    usage_type: AccountUsageType = Field(..., description="The type of AI usage (e.g., translation, image, etc.).")
    usage_id: int = Field(..., description="The ID of the AI-related resource.")
    usage_amount: int = Field(..., description="The number of tokens, words, or items used.")
    credits_amount: Decimal = Field(..., description="The credit cost of the usage.")


class UpdateAccountUsageDTO(BaseUpdateItemDTO):
    """
    DTO used to update account usage.
    """
    usage_type: AccountUsageType | None = Field(None, description="Updated usage type.")
    usage_id: int | None = Field(None, description="Updated usage resource ID.")
    usage_amount: int | None = Field(None, description="Updated number of tokens, words, or items used.")
    credits_amount: Decimal | None = Field(None, description="Updated credit cost of the usage.")


class AccountUsageDTO(BaseItemDTO):
    """
    DTO representing a full view of account usage.
    """
    id: int = Field(..., description="Unique identifier of the account usage.")
    account_id: int = Field(..., description="The ID of the account that performed the usage.")
    usage_type: AccountUsageType = Field(..., description="The type of AI usage performed.")
    usage_id: int = Field(..., description="The ID of the AI-related resource used.")
    usage_amount: int = Field(..., description="The number of tokens, words, or items used.")
    credits_amount: Decimal = Field(..., description="The credit cost charged for the usage.")


class AccountUsageListDTO(BaseItemsListDTO):
    """
    DTO representing a summary of account usage for list views.
    """
    id: int = Field(..., description="Unique identifier of the account usage.")
    usage_type: AccountUsageType = Field(..., description="The type of AI usage performed.")
    usage_amount: int = Field(..., description="The number of tokens, words, or items used.")
    credits_amount: Decimal = Field(..., description="The credit cost charged for the usage.")
