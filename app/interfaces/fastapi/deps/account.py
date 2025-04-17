from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from application.account.services import AccountService
from application.security.token import verify_token
from core.enums.repository.types import RepositoryTypes
from core.messages.exceptions import GetExMessages
from domain.account.exceptions import AccountNotFoundError
from domain.account.entities import AccountEntity

# FastAPI bearer scheme
bearer_scheme = HTTPBearer(auto_error=False)
baerer_scheme_with_raise = HTTPBearer(auto_error=True,
                                      scheme_name="Authorization",
                                      description="JWT Bearer access token. Format: Bearer <token>")


async def get_account_service() -> AccountService:
    """
    Dependency that provides an instance of AccountService with default repository.
    """
    return AccountService(repository_type=RepositoryTypes.TORTOISE)


async def get_current_account(
        credentials: HTTPAuthorizationCredentials = Depends(baerer_scheme_with_raise),
        service: AccountService = Depends(get_account_service),
) -> AccountEntity:
    """
    Dependency to extract and verify the authenticated account from the access token.

    Args:
        credentials: Bearer token from request header.
        service: Injected AccountService instance.

    Returns:
        AccountEntity: The authenticated user account.

    Raises:
        HTTPException 401 if the token is invalid or user not found.
    """
    token = credentials.credentials
    account_id = verify_token(token)

    if not account_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=GetExMessages.invalid_token(),
        )

    try:
        return await service.get_by_id(account_id)
    except AccountNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=GetExMessages.account_not_found(),
        )


async def get_current_account_or_none(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        service: AccountService = Depends(get_account_service),
) -> AccountEntity | None:
    """
    Dependency to extract and verify the authenticated account from the access token.
    Or return None if the token is invalid or user not found.
    Args:
        credentials: Bearer token from request header.
        service: Injected AccountService instance.

    Returns:
        AccountEntity: The authenticated user account or None if user not found.
    """
    if not credentials:
        return None
    token = credentials.credentials
    if not token:
        return None
    account_id = verify_token(token)
    if not account_id:
        return None
    try:
        return await service.get_by_id(account_id)
    except AccountNotFoundError:
        return None


def get_account_func(with_raise=False):
    if with_raise:
        return get_current_account
    return get_current_account_or_none
