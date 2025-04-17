from domain.auth_profile.factories.provider_factory import AuthProviderFactory
from infrastructure.auth.providers.telegram import TelegramAuthProvider


def register_auth_providers():
    """
    Register all external authentication providers for use by the AuthProviderFactory.
    """
    AuthProviderFactory.register(TelegramAuthProvider)
