from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse

from application.events.streaming.wrappers import with_streaming
from application.events.streaming.statuses import StreamingStatuses
from application.events.streaming.types import StreamingTypes
from application.finance.utils.transaction_factory import publish_start_bonus_transaction
from core.datatypes.action_responses import ActionResponse
from domain.account.entities import AccountEntity
from domain.finance.entities import AccountTransactionEntity
from interfaces.fast_api.deps.account import get_current_account
from application.finance.dtos.account_transaction import (CreateAccountTransactionDTO, UpdateAccountTransactionDTO,
                                                          AccountTransactionDTO, AccountTransactionListDTO)
from application.finance.services.account_transaction_service import AccountTransactionService
from interfaces.fast_api.routers.abstract.crud import BaseCRUDApiViewSet

router = APIRouter(prefix="/transaction", tags=["Transactions"])


class AccountTransactionViewSet(BaseCRUDApiViewSet):
    schema = AccountTransactionDTO
    list_schema = AccountTransactionListDTO
    create_schema = CreateAccountTransactionDTO
    update_schema = UpdateAccountTransactionDTO
    service_type = AccountTransactionService
    update_denied = True
    create_denied = True
    get_auth = True

    async def _get_list(self, account: AccountEntity) -> list[AccountTransactionEntity]:
        account_transaction_services = AccountTransactionService()
        return await account_transaction_services.repository.list_by_account(account_id=account.id)


view = AccountTransactionViewSet(router)


@router.post("/start_bonus/", response_model=ActionResponse, responses={
    status.HTTP_200_OK: {"description": "Start bonus granted successfully"},
    status.HTTP_403_FORBIDDEN: {"description": "Start bonus already exists"},
    status.HTTP_408_REQUEST_TIMEOUT: {"description": "Request timeout"}
})
async def start_bonus(account: AccountEntity = Depends(get_current_account)) -> JSONResponse:
    event_streaming = await with_streaming(publish_start_bonus_transaction, StreamingTypes.START_BONUS)(account.id)
    result = await event_streaming.await_statuses()
    success = result.status == StreamingStatuses.SUCCEEDED.value
    status_code = status.HTTP_200_OK if success else status.HTTP_403_FORBIDDEN
    return JSONResponse(
        status_code=status_code,
        content=ActionResponse(success=success, message=result.message).model_dump()
    )


view.set_routes()
