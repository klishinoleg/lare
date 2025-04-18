from fastapi import APIRouter, Depends
from application.account.dtos import AccountDTO
from application.auth.dtos import AuthResponseDTO, AuthProfileDTO
from application.auth.services.auth_via_profile import AuthViaProfileService
from application.auth.services.password_auth_service import PasswordAuthService
from domain.account.entities import AccountEntity
from application.auth.dtos.password import PasswordRegistrationInitDataDTO, PasswordLoginInitDataDTO, \
    ChangePasswordInitDataDTO, PasswordRegistrationDTO, PasswordLoginDTO, ChangePasswordDTO
from domain.auth_profile.enums import AuthProviderType
from infrastructure.auth.dtos.telegram import TelegramAuthInitDataDTO, TelegramProviderDataDTO
from interfaces.fast_api.deps.account import get_current_account
from interfaces.fast_api.deps.auth import get_auth_service, get_password_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram/", response_model=AuthResponseDTO)
async def auth_via_telegram(data: TelegramProviderDataDTO,
                            service: AuthViaProfileService = Depends(get_auth_service)) -> AuthResponseDTO:
    """
    Authenticate or register user via Telegram WebApp.

    - Validates Telegram init_data from WebApp
    - If the user profile exists, returns user and JWT token
    - If not, creates user and links auth profile
    - Returns: token + account data

    Args:
        data (TelegramProviderDataDTO): Validated Telegram init data

    Returns:
        AuthResponseDTO: {
            token: JWT token string,
            user: AccountDTO
        }
        :param data:
        :param service:
    """
    telegram_init_dto = TelegramAuthInitDataDTO(provider_data=data, provider_type=AuthProviderType.TELEGRAM)
    return await service.authenticate(telegram_init_dto)


@router.get("/me/", response_model=AccountDTO)
async def get_me(account: AccountEntity = Depends(get_current_account)) -> AccountDTO:
    """
    Get current authenticated user info.

    Returns:
        AccountDTO: Account information of the authenticated user.
    """
    return AccountDTO.create_from_dict(account.to_dict())


@router.get("/profiles/", response_model=list[AuthProfileDTO])
async def get_profiles(
        account: AccountEntity = Depends(get_current_account),
        service: AuthViaProfileService = Depends(get_auth_service)
) -> list[AuthProfileDTO]:
    """
    Get current authenticated user profiles.
    :param service:
    :param account:
    :return: list[AuthProfileDTO]
    """
    return await service.get_profiles(account_id=account.id)


@router.post("/register/", response_model=AuthResponseDTO)
async def register_user(
        data: PasswordRegistrationDTO,
        service: PasswordAuthService = Depends(get_password_service),
) -> AuthResponseDTO:
    init_dto = PasswordRegistrationInitDataDTO(provider_data=data)
    return await service.register(init_dto)


@router.post("/login/", response_model=AuthResponseDTO)
async def login_user(
        data: PasswordLoginDTO,
        service: PasswordAuthService = Depends(get_password_service),
) -> AuthResponseDTO:
    init_data = PasswordLoginInitDataDTO(provider_data=data)
    return await service.login(init_data)


@router.post("/change_password/", response_model=AuthResponseDTO)
async def change_password(
        data: ChangePasswordDTO,
        account: AccountEntity = Depends(get_current_account),
        service: PasswordAuthService = Depends(get_password_service)
) -> AuthResponseDTO:
    init_dto = ChangePasswordInitDataDTO(provider_data=data)
    return await service.change_password(init_dto, account)
