from application.auth.services.password_auth_service import PasswordAuthService
from core.enums.repository.types import RepositoryTypes
from application.auth.services.auth_via_profile import AuthViaProfileService


async def get_auth_service() -> AuthViaProfileService:
    """
    Dependency that provides an instance of AccountService with default repository.
    """
    return AuthViaProfileService(repository_type=RepositoryTypes.TORTOISE)


async def get_password_service() -> PasswordAuthService:
    """
    Dependency that provides an instance of AccountService with default repository.
    :return: PasswordAuthService
    """
    return PasswordAuthService(repository_type=RepositoryTypes.TORTOISE)
