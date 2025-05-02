from __future__ import annotations
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from application.abstract.dtos import BaseCreateItemDTO, BaseUpdateItemDTO, BaseItemsListDTO, BaseItemDTO


class CreateAccountDTO(BaseCreateItemDTO):
    """
    DTO used for creating a new user account.
    """
    username: str = Field(..., description="Unique username for the account")
    email: str | None = Field(None, description="Optional email address")
    public_name: str | None = Field(None, description="Optional display name shown to others")


class AccountDTO(BaseItemDTO):
    """
    Full representation of an account returned in responses.
    """
    id: int = Field(..., description="Unique identifier of the account")
    username: str = Field(..., description="Account's unique username")
    email: str | None = Field(None, description="Email address of the user")
    public_name: str | None = Field(None, description="Display name shown to other users")
    created_at: datetime = Field(..., description="Timestamp when the account was created")
    updated_at: datetime = Field(..., description="Timestamp of the last account update")
    is_active: bool = Field(..., description="Indicates if the account is currently active")
    credits: Decimal = Field(..., description="Current credit balance of the account")


class AccountListDTO(BaseItemsListDTO):
    """
    Lightweight representation of an account used in lists.
    """
    id: int = Field(..., description="Unique identifier of the account")
    username: str = Field(..., description="Username of the account")


class UpdateAccountDTO(BaseUpdateItemDTO):
    """
    DTO used for updating an existing account.
    """
    username: str | None = Field(None, description="New username (if updated)")
    email: str | None = Field(None, description="New email address (if updated)")
    public_name: str | None = Field(None, description="New public display name (if updated)")
